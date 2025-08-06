import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.database import client, collection
from routes import webhook, messages, websocket

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Starting FastAPI app...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Connect to MongoDB
    try:
        logger.debug("Attempting MongoDB connection...")
        await client.admin.command('ping')  # Test MongoDB connection
        logger.info("MongoDB connected successfully")
    except Exception as e:
        logger.error(f"MongoDB connection failed: {str(e)}")
        raise
    yield
    # Shutdown: Close MongoDB connection
    client.close()
    logger.info("MongoDB disconnected")

app = FastAPI(title="WhatsApp Web Clone API", lifespan=lifespan)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://your-frontend-url"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(webhook.router, prefix="/api")
app.include_router(messages.router, prefix="/api")
app.include_router(websocket.router, prefix="/api")

@app.get("/")
async def root():
    return {"message": "WhatsApp Web Clone API"}

@app.get("/test-db")
async def test_db():
    try:
        await collection.insert_one({"test": "ping"})
        result = await collection.find_one({"test": "ping"})
        logger.debug(f"Test DB result: {result}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Test DB failed: {str(e)}")
        return {"status": "error", "message": str(e)}