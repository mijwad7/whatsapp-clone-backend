from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
import json
from typing import Dict, List
from fastapi.encoders import jsonable_encoder

router = APIRouter()

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client["whatsapp"]
messages_collection = db["processed_messages"]

# Store active WebSocket connections by wa_id
active_connections: Dict[str, List[WebSocket]] = {}

async def broadcast_message(wa_id: str, message: Dict):
    """Broadcast message to all clients subscribed to wa_id."""
    if wa_id in active_connections:
        for connection in active_connections[wa_id]:
            await connection.send_json(jsonable_encoder(message))

@router.websocket("/api/ws/{wa_id}")
async def websocket_endpoint(websocket: WebSocket, wa_id: str):
    await websocket.accept()
    
    # Add connection to active_connections
    if wa_id not in active_connections:
        active_connections[wa_id] = []
    active_connections[wa_id].append(websocket)
    
    try:
        # Send confirmation
        await websocket.send_json({"status": "connected", "wa_id": wa_id})
        
        # Watch for changes in processed_messages for this wa_id
        async with messages_collection.watch(
            [{"$match": {"operationType": {"$in": ["insert", "update"]}, "fullDocument.wa_id": wa_id}}]
        ) as change_stream:
            async for change in change_stream:
                if change["operationType"] == "insert":
                    message = change["fullDocument"]
                    message["_id"] = str(message["_id"])
                    await broadcast_message(wa_id, message)
                elif change["operationType"] == "update":
                    message = change["fullDocument"]
                    message["_id"] = str(message["_id"])
                    await broadcast_message(wa_id, message)
                
                # Keep connection alive
                await websocket.send_json({"ping": "pong"})
                
    except WebSocketDisconnect:
        # Remove connection on disconnect
        active_connections[wa_id].remove(websocket)
        if not active_connections[wa_id]:
            del active_connections[wa_id]
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
    finally:
        if wa_id in active_connections and websocket in active_connections[wa_id]:
            active_connections[wa_id].remove(websocket)
            if not active_connections[wa_id]:
                del active_connections[wa_id]