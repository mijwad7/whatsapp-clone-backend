import json
import asyncio
import os
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from datetime import datetime
from fastapi.encoders import jsonable_encoder
from typing import Dict, Any

async def broadcast_message(wa_id: str, message: Dict):
    """Placeholder to simulate WebSocket broadcast (integrates with websocket.py)."""
    print(f"Broadcasting to wa_id {wa_id}: {message}")

async def process_payload(file_path: str, messages_collection, conversations_collection):
    try:
        with open(file_path, 'r') as f:
            payload = json.load(f)
        
        print(f"Processing payload: {file_path}")
        
        # Check for entry in metaData or directly in payload
        entry = payload.get("metaData", {}).get("entry") or payload.get("entry")
        if not entry:
            print(f"Invalid payload in {file_path}: missing entry")
            return
        
        entry = entry[0] if isinstance(entry, list) else entry
        if "changes" not in entry or not entry["changes"]:
            print(f"Invalid payload in {file_path}: missing changes")
            return
        
        change = entry["changes"][0]
        value = change.get("value", {})
        if not value:
            print(f"Invalid payload in {file_path}: missing value")
            return
        
        # Handle messages
        messages = value.get("messages", [])
        for message in messages:
            wa_id = message.get("from")
            text = message.get("text", {}).get("body")
            message_id = message.get("id")
            if wa_id and text and message_id:
                new_message = {
                    "wa_id": wa_id,
                    "text": text,
                    "timestamp": datetime.utcnow(),
                    "status": "received",
                    "message_id": message_id
                }
                await messages_collection.insert_one(new_message)
                print(f"Inserted message: {new_message}")
                
                # Update conversation
                await conversations_collection.update_one(
                    {"wa_id": wa_id},
                    {"$set": {"last_message": text, "timestamp": datetime.utcnow()}},
                    upsert=True
                )
                print(f"Updated conversation for wa_id: {wa_id}")
                
                # Broadcast to WebSocket clients
                new_message["_id"] = str(new_message["_id"])
                await broadcast_message(wa_id, new_message)
        
        # Handle statuses
        statuses = value.get("statuses", [])
        for status in statuses:
            message_id = status.get("id") or status.get("meta_msg_id")
            status_value = status.get("status")
            wa_id = status.get("recipient_id")
            if message_id and status_value in ["sent", "delivered", "read"]:
                result = await messages_collection.update_one(
                    {"message_id": message_id},
                    {"$set": {"status": status_value, "timestamp": datetime.utcnow()}}
                )
                if result.modified_count > 0:
                    print(f"Updated status for message_id {message_id} to {status_value}")
                    # Fetch updated message for broadcast
                    updated_message = await messages_collection.find_one({"message_id": message_id})
                    if updated_message:
                        updated_message["_id"] = str(updated_message["_id"])
                        await broadcast_message(wa_id, updated_message)
                else:
                    print(f"No message found with message_id {message_id}")
    
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")

async def main():
    load_dotenv()
    MONGODB_URL = os.getenv("MONGODB_URL")
    client = AsyncIOMotorClient(MONGODB_URL)
    try:
        await client.admin.command('ping')
        print("MongoDB connected successfully")
        
        db = client["whatsapp"]
        messages_collection = db["processed_messages"]
        conversations_collection = db["conversations"]
        
        payload_dir = Path(__file__).parent / "sample_payloads"
        for file_path in payload_dir.glob("*.json"):
            await process_payload(str(file_path), messages_collection, conversations_collection)
    
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
    finally:
        client.close()
        print("MongoDB disconnected")

if __name__ == "__main__":
    asyncio.run(main())