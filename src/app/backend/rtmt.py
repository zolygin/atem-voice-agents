import aiohttp
import asyncio
import json
from typing import Any, Optional
from aiohttp import ClientWebSocketResponse, web
from azure.identity import DefaultAzureCredential, AzureDeveloperCliCredential, get_bearer_token_provider
from azure.core.credentials import AzureKeyCredential
from backend.tools.tools import Tool
from backend.rtmt_message_processor import RTMessageProcessor

class RTMiddleTier:
    endpoint: str
    deployment: str
    key: Optional[str] = None
    selected_voice: str = "alloy"

    # Tools are server-side only for now, though the case could be made for client-side tools
    # in addition to server-side tools that are invisible to the client
    tools: dict[str, Tool] = {}

    # Server-enforced configuration, if set, these will override the client's configuration
    # Typically at least the model name and system message will be set by the server
    model: Optional[str] = None
    system_message: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    disable_audio: Optional[bool] = None

    _token_provider = None
    _message_processor: RTMessageProcessor

    def __init__(self, endpoint: str, deployment: str, credentials: AzureKeyCredential | AzureDeveloperCliCredential | DefaultAzureCredential):
        self.endpoint = endpoint
        self.deployment = deployment
        if isinstance(credentials, AzureKeyCredential):
            self.key = credentials.key
        else:
            self._token_provider = get_bearer_token_provider(credentials, "https://cognitiveservices.azure.com/.default")
            self._token_provider() # Warm up during startup so we have a token cached when the first request arrives

        self._message_processor = RTMessageProcessor(self.tools)

    async def forward_messages(self, ws: web.WebSocketResponse, is_acs_audio_stream: bool):
        session = None
        target_ws = None
        try:
            session = aiohttp.ClientSession(base_url=self.endpoint)
            params = { "api-version": "2024-10-01-preview", "deployment": self.deployment }

            headers = {}
            if "x-ms-client-request-id" in ws.headers:
                headers["x-ms-client-request-id"] = ws.headers["x-ms-client-request-id"]

            # Setup authentication headers for the OpenAI Realtime API WebSocket connection
            if self.key is not None:
                headers = { "api-key": self.key }
            else:
                if self._token_provider is not None:
                    headers = { "Authorization": f"Bearer {self._token_provider()}" } # NOTE: no async version of token provider, maybe refresh token on a timer?
                else:
                    raise ValueError("No token provider available")

            # Connect to the OpenAI Realtime API WebSocket
            target_ws = await session.ws_connect("/openai/realtime", headers=headers, params=params)
            
            async def from_client_to_server():
                # Messages from Azure Communication Services or the Web Frontend are forwarded to the OpenAI Realtime API
                try:
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._message_processor.process_message_to_server(
                                data, ws, target_ws, is_acs_audio_stream,
                                self.model, self.system_message, self.temperature, 
                                self.max_tokens, self.disable_audio, self.selected_voice
                            )
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("Client WebSocket closed")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("Client WebSocket error:", ws.exception())
                            break
                        else:
                            print("Error: unexpected message type:", msg.type)
                except Exception as e:
                    print(f"Error in client-to-server forwarding: {e}")

            async def from_server_to_client():
                # Messages from the OpenAI Realtime API are forwarded to the Azure Communication Services or the Web Frontend
                try:
                    async for msg in target_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._message_processor.process_message_to_client(
                                data, ws, target_ws, is_acs_audio_stream
                            )
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("Server WebSocket closed")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print("Server WebSocket error:", target_ws.exception())
                            break
                        else:
                            print("Error: unexpected message type:", msg.type)
                except Exception as e:
                    print(f"Error in server-to-client forwarding: {e}")

            # Run both forwarding tasks concurrently
            await asyncio.gather(from_client_to_server(), from_server_to_client())
            
        except Exception as e:
            print(f"Error in forward_messages: {e}")
        finally:
            # Clean up WebSocket connections
            if target_ws and not target_ws.closed:
                await target_ws.close()
            if session and not session.closed:
                await session.close()
            print("WebSocket connections cleaned up")
