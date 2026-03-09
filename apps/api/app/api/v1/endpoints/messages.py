"""
Messages API Endpoints
"""

from typing import AsyncGenerator
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import json
import asyncio
import structlog

from commons.types.requests import MessageRequest
from commons.types.responses import MessageResponse, StreamingMessageResponse
from ....dependencies import get_message_service
from ....services.message_service import MessageService
from ....websocket_manager import ws_manager

logger = structlog.get_logger()
router = APIRouter()


@router.post("/", response_model=MessageResponse)
async def send_message(
    request: MessageRequest,
    message_service: MessageService = Depends(get_message_service)
):
    """Send a message and get a response."""
    try:
        response = await message_service.process_message(request)
        return response
    except Exception as e:
        logger.error("Error processing message", error=str(e))
        raise HTTPException(status_code=500, detail="Error processing message")


@router.post("/stream")
async def stream_message(
    request: MessageRequest,
    message_service: MessageService = Depends(get_message_service)
):
    """Send a message and get a streaming response."""
    async def generate_stream():
        try:
            async for chunk in message_service.stream_message(request):
                # Manual SSE formatting: "data: <json>\n\n"
                data = f"data: {chunk.model_dump_json()}\n\n"
                yield data
                # Small delay to ensure proper streaming and prevent buffering
                await asyncio.sleep(0.01)
        except Exception as e:
            logger.error("Error streaming message", error=str(e))
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        }
    )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    message_service: MessageService = Depends(get_message_service)
):
    """WebSocket endpoint for real-time messaging."""
    await websocket.accept()
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                # Heartbeat ping — respond immediately and wait for next message
                if request_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
                    continue
                request = MessageRequest(**request_data)
            except (json.JSONDecodeError, ValueError) as e:
                await websocket.send_text(json.dumps({
                    "error": "Invalid message format",
                    "detail": str(e)
                }))
                continue
            
            # Process message and stream response
            try:
                async for chunk in message_service.stream_message(request):
                    await websocket.send_text(chunk.model_dump_json())
            except Exception as e:
                logger.error("Error processing WebSocket message", error=str(e))
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "content": f"Error: {str(e)}",
                    "conversation_id": request.conversation_id or "",
                }))
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error("WebSocket error", error=str(e))
        await websocket.close(code=1011, reason="Internal error")


@router.websocket("/ws/admin/{conversation_id}")
async def admin_websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    message_service: MessageService = Depends(get_message_service),
):
    """Admin WebSocket for human takeover and live conversation monitoring."""
    await ws_manager.connect_admin(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "take_control":
                ws_manager.set_human_control(conversation_id, True)
                await ws_manager.send_to_admin(conversation_id, {
                    "type": "control_status",
                    "is_human_in_control": True,
                })
                await ws_manager.send_to_admin(conversation_id, {
                    "type": "system_notice",
                    "content": "You took control of this conversation",
                })
                await ws_manager.send_to_widget(conversation_id, {
                    "type": "control_status",
                    "is_human_in_control": True,
                })
                await ws_manager.send_to_widget(conversation_id, {
                    "type": "system_notice",
                    "content": "Conversation switched to Human mode",
                })

            elif msg_type == "release_control":
                # Collect buffered takeover messages before clearing state
                takeover_messages = ws_manager.pop_takeover_buffer(conversation_id)
                ws_manager.set_human_control(conversation_id, False)

                await ws_manager.send_to_admin(conversation_id, {
                    "type": "control_status",
                    "is_human_in_control": False,
                })
                await ws_manager.send_to_admin(conversation_id, {
                    "type": "system_notice",
                    "content": "Control returned to AI",
                })
                await ws_manager.send_to_widget(conversation_id, {
                    "type": "control_status",
                    "is_human_in_control": False,
                })
                await ws_manager.send_to_widget(conversation_id, {
                    "type": "system_notice",
                    "content": "Conversation switched to AI mode",
                })

                # Inject takeover messages into AI memory so it has full context
                agent_id = ws_manager.get_agent_id(conversation_id)
                if agent_id and takeover_messages:
                    asyncio.create_task(
                        message_service.inject_history(conversation_id, agent_id, takeover_messages),
                        name=f"inject_history_{conversation_id}",
                    )

            elif msg_type == "admin_message":
                content = msg.get("content", "")
                # Deliver to widget
                await ws_manager.send_to_widget(conversation_id, {
                    "type": "admin_message",
                    "role": "assistant",
                    "content": content,
                })
                # Buffer for memory injection on release
                ws_manager.buffer_takeover_message(conversation_id, "assistant", content)
                # Persist to Strapi (role 'agent' matches Strapi convention)
                message_service.strapi.save_message(conversation_id, content, "agent")

    except WebSocketDisconnect:
        logger.info("Admin WebSocket disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("Admin WebSocket error", error=str(e), conversation_id=conversation_id)
    finally:
        ws_manager.disconnect_admin(websocket, conversation_id)


@router.websocket("/ws/widget/{conversation_id}")
async def widget_control_channel(
    websocket: WebSocket,
    conversation_id: str,
    message_service: MessageService = Depends(get_message_service),
):
    """Widget control channel — registers widget with ws_manager so admin can push to it.

    Receives:
    - register: widget sends agent_id so backend can restore AI context on release
    - ping: heartbeat
    - user_message: forwarded to admin during human takeover, buffered, and persisted
    """
    await ws_manager.connect_widget(websocket, conversation_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")

            if msg_type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))

            elif msg_type == "register":
                # Widget sends its agent_id so we can inject history into the right memory
                agent_id = msg.get("agent_id", "")
                if agent_id:
                    ws_manager.register_agent_id(conversation_id, agent_id)

            elif msg_type == "user_message":
                if ws_manager.is_human_in_control(conversation_id):
                    content = msg.get("content", "")
                    # Deliver to admin dashboard in real-time
                    await ws_manager.send_to_admin(conversation_id, {
                        "type": "user_message",
                        "role": "user",
                        "content": content,
                    })
                    # Buffer for memory injection on release
                    ws_manager.buffer_takeover_message(conversation_id, "user", content)
                    # Persist to Strapi
                    message_service.strapi.save_message(conversation_id, content, "user")

    except WebSocketDisconnect:
        logger.info("Widget control channel disconnected", conversation_id=conversation_id)
    except Exception as e:
        logger.error("Widget control channel error", error=str(e), conversation_id=conversation_id)
    finally:
        ws_manager.disconnect_widget(websocket, conversation_id)
