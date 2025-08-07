import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from bson import ObjectId
from fastapi.encoders import jsonable_encoder
from routes import webhook, messages, websocket

# Suppress pymongo.topology logs
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("pymongo.topology").setLevel(logging.WARNING)

# Configure application logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
print("Starting FastAPI app...")
logger.debug("Starting FastAPI app...")

load_dotenv()
MONGODB_URL = os.getenv("MONGODB_URL")
client = AsyncIOMotorClient(MONGODB_URL)
database = client["whatsapp_clone"]
collection = database["messages"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting lifespan handler...")
    try:
        print("Attempting MongoDB connection...")
        await client.admin.command('ping')
        print("MongoDB connected successfully")
        logger.info("MongoDB connected successfully")
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise
    yield
    client.close()
    print("MongoDB disconnected")
    logger.info("MongoDB disconnected")

app = FastAPI(title="WhatsApp Web Clone API", lifespan=lifespan)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-frontend-url"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(webhook.router)
app.include_router(messages.router)
app.include_router(websocket.router)

@app.get("/")
async def root():
    return {"message": "WhatsApp Web Clone API"}

@app.get("/test-db")
async def test_db():
    try:
        await collection.insert_one({"test": "ping"})
        result = await collection.find_one({"test": "ping"})
        # Convert ObjectId to string for JSON serialization
        if result:
            result["_id"] = str(result["_id"])
        print(f"Test DB result: {result}")
        logger.debug(f"Test DB result: {result}")
        return {"status": "success", "result": jsonable_encoder(result)}
    except Exception as e:
        print(f"Test DB failed: {str(e)}")
        logger.error(f"Test DB failed: {str(e)}", exc_info=True)
        raise