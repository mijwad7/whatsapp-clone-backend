from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from typing import Dict, Any
from datetime import datetime
from bson import ObjectId

router = APIRouter()

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client["whatsapp"]
messages_collection = db["processed_messages"]
conversations_collection = db["conversations"]


@router.post("/api/webhook")
async def webhook_endpoint(payload: Dict[Any, Any]):
    try:
        print(f"Received webhook payload: {payload}")

        # Check for entry in metaData or directly in payload
        entry = payload.get("metaData", {}).get("entry") or payload.get("entry")
        if not entry:
            raise HTTPException(
                status_code=400, detail="Invalid payload: missing entry"
            )

        entry = entry[0] if isinstance(entry, list) else entry
        if "changes" not in entry or not entry["changes"]:
            raise HTTPException(
                status_code=400, detail="Invalid payload: missing changes"
            )

        change = entry["changes"][0]
        value = change.get("value", {})
        if not value:
            raise HTTPException(
                status_code=400, detail="Invalid payload: missing value"
            )

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
                    "message_id": message_id,
                }
                await messages_collection.insert_one(new_message)
                # Update conversation
                await conversations_collection.update_one(
                    {"wa_id": wa_id},
                    {"$set": {"last_message": text, "timestamp": datetime.utcnow()}},
                    upsert=True,
                )

        # Handle statuses
        statuses = value.get("statuses", [])
        for status in statuses:
            message_id = status.get("id") or status.get("meta_msg_id")
            status_value = status.get("status")
            if message_id and status_value in ["sent", "delivered", "read"]:
                await messages_collection.update_one(
                    {"message_id": message_id},
                    {"$set": {"status": status_value, "timestamp": datetime.utcnow()}},
                )

        return {"status": "received"}
    except Exception as e:
        print(f"Webhook processing failed: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )


