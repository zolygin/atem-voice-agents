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
        client_to_server_task = None
        server_to_client_task = None
        
        try:
            # Create client session with timeout configuration
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            session = aiohttp.ClientSession(base_url=self.endpoint, timeout=timeout)
            params = { "api-version": "2024-10-01-preview", "deployment": self.deployment }

            headers = {}
            if "x-ms-client-request-id" in ws.headers:
                headers["x-ms-client-request-id"] = ws.headers["x-ms-client-request-id"]

            # Setup authentication headers for the OpenAI Realtime API WebSocket connection
            if self.key is not None:
                headers = { "api-key": self.key }
            else:
                if self._token_provider is not None:
                    headers = { "Authorization": f"Bearer {self._token_provider()}" }
                else:
                    raise ValueError("No token provider available")

            # Connect to the OpenAI Realtime API WebSocket with timeout
            target_ws = await session.ws_connect("/openai/realtime", headers=headers, params=params, timeout=10)
            print(f"Connected to OpenAI Realtime API: {self.endpoint}")
            
            async def from_client_to_server():
                """Forward messages from client WebSocket to OpenAI Realtime API"""
                try:
                    async for msg in ws:
                        if ws.closed:
                            print("Client WebSocket closed during iteration")
                            break
                            
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                await self._message_processor.process_message_to_server(
                                    data, ws, target_ws, is_acs_audio_stream,
                                    self.model, self.system_message, self.temperature, 
                                    self.max_tokens, self.disable_audio, self.selected_voice
                                )
                            except json.JSONDecodeError as e:
                                print(f"Error decoding client message: {e}")
                            except Exception as e:
                                print(f"Error processing client message: {e}")
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("Client WebSocket closed (CLOSED)")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"Client WebSocket error: {ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSING:
                            print("Client WebSocket closing")
                            break
                        else:
                            print(f"Unexpected client message type: {msg.type}")
                except asyncio.CancelledError:
                    print("Client-to-server task cancelled")
                    raise
                except Exception as e:
                    print(f"Error in client-to-server forwarding: {e}")
                finally:
                    print("Client-to-server forwarding task finished")

            async def from_server_to_client():
                """Forward messages from OpenAI Realtime API to client WebSocket"""
                try:
                    async for msg in target_ws:
                        if target_ws.closed:
                            print("Server WebSocket closed during iteration")
                            break
                            
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            try:
                                data = json.loads(msg.data)
                                await self._message_processor.process_message_to_client(
                                    data, ws, target_ws, is_acs_audio_stream
                                )
                            except json.JSONDecodeError as e:
                                print(f"Error decoding server message: {e}")
                            except Exception as e:
                                print(f"Error processing server message: {e}")
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            print("Server WebSocket closed (CLOSED)")
                            break
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"Server WebSocket error: {target_ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSING:
                            print("Server WebSocket closing")
                            break
                        else:
                            print(f"Unexpected server message type: {msg.type}")
                except asyncio.CancelledError:
                    print("Server-to-client task cancelled")
                    raise
                except Exception as e:
                    print(f"Error in server-to-client forwarding: {e}")
                finally:
                    print("Server-to-client forwarding task finished")

            # Create tasks for both directions
            client_to_server_task = asyncio.create_task(from_client_to_server())
            server_to_client_task = asyncio.create_task(from_server_to_client())
            
            # Wait for either task to complete or be cancelled
            done, pending = await asyncio.wait(
                [client_to_server_task, server_to_client_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancel any remaining tasks
            for task in pending:
                if not task.done():
                    print(f"Cancelling pending task: {task}")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        print("Task cancelled successfully")
                    except Exception as e:
                        print(f"Error while cancelling task: {e}")
            
            # Check results of completed tasks
            for task in done:
                try:
                    await task
                except asyncio.CancelledError:
                    print("Task was cancelled")
                except Exception as e:
                    print(f"Task completed with error: {e}")
                    
        except asyncio.CancelledError:
            print("forward_messages cancelled")
        except Exception as e:
            print(f"Error in forward_messages: {e}")
        finally:
            # Clean up all resources
            print("Cleaning up WebSocket connections and sessions...")
            
            # Cancel any remaining tasks
            tasks_to_cancel = []
            if client_to_server_task and not client_to_server_task.done():
                tasks_to_cancel.append(client_to_server_task)
            if server_to_client_task and not server_to_client_task.done():
                tasks_to_cancel.append(server_to_client_task)
                
            if tasks_to_cancel:
                for task in tasks_to_cancel:
                    task.cancel()
                try:
                    await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
                except Exception as e:
                    print(f"Error cancelling tasks: {e}")
            
            # Close WebSocket connections
            if target_ws and not target_ws.closed:
                try:
                    await target_ws.close()
                    print("Server WebSocket closed")
                except Exception as e:
                    print(f"Error closing server WebSocket: {e}")
            
            # Close client session
            if session:
                try:
                    await session.close()
                    print("Client session closed")
                except Exception as e:
                    print(f"Error closing client session: {e}")
            
            print("All WebSocket connections and sessions cleaned up")
