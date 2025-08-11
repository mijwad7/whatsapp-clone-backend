# WhatsApp Clone Backend

This is the backend for a WhatsApp Web clone, built with FastAPI, MongoDB, and WebSocket support for real-time messaging. It processes WhatsApp Business API-like webhook payloads, stores messages and conversations, and serves a React frontend.

## Features
- **Webhook Processing**: Handles message and status payloads, storing them in MongoDB (`processed_messages` and `conversations` collections).
- **API Endpoints**: Provides `/api/conversations`, `/api/messages/{wa_id}`, and `/api/send-message` for chat functionality.
- **WebSocket**: Real-time message and status updates via `/api/ws/{wa_id}`.
- **MongoDB**: Integrates with MongoDB Atlas for persistent storage.

## Prerequisites
- Python 3.11+
- MongoDB Atlas account
- Git
- Render account (for deployment)

## Setup
1. **Clone Repository**:
   ```bash
   git clone <your-backend-repo-url>
   cd whatsapp-clone-backend
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   - Create `.env` in the root directory:
     ```
     MONGODB_URL=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/whatsapp?retryWrites=true&w=majority
     ```
   - Ensure MongoDB Atlas allows `readWrite@whatsapp`.

5. **Process Sample Payloads**:
   - Sample payloads are included in the `sample_payloads` directory.
   - Run:
     ```bash
     python process_webhook_payloads.py
     ```

6. **Run Locally**:
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```
   - Access API at `http://localhost:8000/api/conversations`.
   - Test WebSocket with `wscat -c ws://localhost:8000/api/ws/918329446654`.

## Deployment on Render
1. Push to GitHub:
   ```bash
   git push origin main
   ```

2. Create Web Service:
   - In [Render Dashboard](https://dashboard.render.com), select **New > Web Service**.
   - Choose `whatsapp-clone-backend` repo.
   - Configure:
     - **Name**: `whatsapp-clone-backend`
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables**:
       - `MONGODB_URL`: Your MongoDB Atlas URL
       - `PYTHON_VERSION`: `3.11`
     - **Instance Type**: Free (testing) or Starter ($7/month) for WebSocket.

3. Process Payloads:
   - After deployment, SSH into the Render instance or run locally to process `sample_payloads`:
     ```bash
     python process_webhook_payloads.py
     ```

4. Verify:
   - Visit `<backend-url>/api/conversations`.
   - Expect `wa_id: 918329446654` with “Hi Neha! ...”.

## API Endpoints
- `GET /api/conversations`: List all conversations.
- `GET /api/messages/{wa_id}`: Get messages for a `wa_id`.
- `POST /api/send-message`: Send a message (body: `{ "wa_id": string, "text": string }`).
- `POST /api/webhook`: Process webhook payloads.
- `WS /api/ws/{wa_id}`: WebSocket for real-time updates.


   - Performance optimization?

Share results and your preference for the next task!
