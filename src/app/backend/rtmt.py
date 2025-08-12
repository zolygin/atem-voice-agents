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
        async with aiohttp.ClientSession(base_url=self.endpoint) as session:
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
            async with session.ws_connect("/openai/realtime", headers=headers, params=params) as target_ws:
                async def from_client_to_server():
                    # Messages from Azure Communication Services or the Web Frontend are forwarded to the OpenAI Realtime API
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._message_processor.process_message_to_server(
                                data, ws, target_ws, is_acs_audio_stream,
                                self.model, self.system_message, self.temperature, 
                                self.max_tokens, self.disable_audio, self.selected_voice
                            )
                        else:
                            print("Error: unexpected message type:", msg.type)

                async def from_server_to_client():
                    # Messages from the OpenAI Realtime API are forwarded to the Azure Communication Services or the Web Frontend
                    async for msg in target_ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            await self._message_processor.process_message_to_client(
                                data, ws, target_ws, is_acs_audio_stream
                            )
                        else:
                            print("Error: unexpected message type:", msg.type)

                try:
                    await asyncio.gather(from_client_to_server(), from_server_to_client())
                except ConnectionResetError:
                    # Ignore the errors resulting from the client disconnecting the socket
                    pass
