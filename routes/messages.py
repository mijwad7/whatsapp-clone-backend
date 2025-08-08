from fastapi import APIRouter, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
from dotenv import load_dotenv
from typing import List, Dict
from datetime import datetime
from fastapi.encoders import jsonable_encoder

router = APIRouter()

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
db = client["whatsapp"]
collection = db["processed_messages"]
conversations_collection = db["conversations"]

@router.get("/api/conversations", response_model=List[Dict])
async def get_conversations():
    try:
        conversations = []
        async for conv in conversations_collection.find():
            conv["_id"] = str(conv["_id"])
            conversations.append(conv)
        return jsonable_encoder(conversations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching conversations: {str(e)}")

@router.get("/api/messages/{wa_id}", response_model=List[Dict])
async def get_messages(wa_id: str):
    try:
        messages = []
        async for msg in collection.find({"wa_id": wa_id}):
            msg["_id"] = str(msg["_id"])
            messages.append(msg)
        return jsonable_encoder(messages)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching messages: {str(e)}")

@router.post("/api/send-message")
async def send_message(message: Dict):
    try:
        wa_id = message.get("wa_id")
        text = message.get("text")
        if not wa_id or not text:
            raise HTTPException(status_code=400, detail="wa_id and text are required")
        new_message = {
            "wa_id": wa_id,
            "text": text,
            "timestamp": datetime.utcnow(),
            "status": "sent",
            "message_id": str(ObjectId())
        }
        await collection.insert_one(new_message)
        # Update conversation
        await conversations_collection.update_one(
            {"wa_id": wa_id},
            {"$set": {"last_message": text, "timestamp": datetime.utcnow()}},
            upsert=True
        )
        new_message["_id"] = str(new_message["_id"])
        return jsonable_encoder(new_message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")