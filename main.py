import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx

app = FastAPI()

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
        
        response = await client.post(API_URL, json=data, headers=headers)
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
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
    response = await send_message(prompt.prompt)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)