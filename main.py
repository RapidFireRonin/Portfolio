from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import os
import logging

app = FastAPI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = os.getenv("ANTHROPIC_API_KEY")
API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

class Prompt(BaseModel):
    prompt: str

async def send_message(prompt: str):
    async with httpx.AsyncClient() as client:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY,
            "anthropic-version": ANTHROPIC_VERSION
        }
        
        data = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        try:
            response = await client.post(API_URL, json=data, headers=headers)
            response.raise_for_status()
            return response.json()["content"][0]["text"]
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    logger.info("Home route accessed")
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Claude Haiku Chat</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                background-color: #f0f0f0;
            }
            .chat-container {
                width: 80%;
                max-width: 600px;
                height: 80vh;
                border: 1px solid #ccc;
                border-radius: 8px;
                overflow: hidden;
                display: flex;
                flex-direction: column;
                background-color: white;
            }
            #chat-messages {
                flex-grow: 1;
                overflow-y: auto;
                padding: 20px;
            }
            .input-area {
                display: flex;
                padding: 10px;
                border-top: 1px solid #ccc;
            }
            #user-input {
                flex-grow: 1;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                margin-left: 10px;
                cursor: pointer;
            }
            .message {
                margin-bottom: 10px;
                padding: 10px;
                border-radius: 4px;
                background-color: #f1f1f1;
            }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <div id="chat-messages"></div>
            <div class="input-area">
                <input type="text" id="user-input" placeholder="Type your message...">
                <button onclick="sendMessage()">Send</button>
            </div>
        </div>

        <script>
            async function sendMessage() {
                const input = document.getElementById('user-input');
                const message = input.value.trim();
                if (message) {
                    addMessage('You', message);
                    try {
                        const response = await fetch('/send', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({prompt: message}),
                        });
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        const data = await response.json();
                        addMessage('Claude', data.response);
                    } catch (error) {
                        console.error('Error:', error);
                        addMessage('Error', 'Failed to get response');
                    }
                    input.value = '';
                }
            }

            function addMessage(sender, text) {
                const chatMessages = document.getElementById('chat-messages');
                const messageElement = document.createElement('div');
                messageElement.className = 'message';
                messageElement.innerHTML = `<strong>${sender}:</strong> ${text}`;
                chatMessages.appendChild(messageElement);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }

            document.getElementById('user-input').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    sendMessage();
                }
            });
        </script>
    </body>
    </html>
    """

@app.post("/send")
async def send(prompt: Prompt):
    logger.info(f"Received prompt: {prompt.prompt}")
    response = await send_message(prompt.prompt)
    logger.info(f"Sent response: {response[:100]}...")  # Log first 100 chars of response
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
