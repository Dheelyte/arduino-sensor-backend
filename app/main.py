import asyncio
import time

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from mangum import Mangum


app = FastAPI(
    title="Arduino Sensor API",
    description="Send and receive sensor data from an Arduino device - By NSChE Hackathon Winning Team",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Store last reading in memory
latest_reading = {
    "temperature": None,
    "humidity": None,
    "vibration": None,
    "timestamp": None
}


class SensorData(BaseModel):
    temperature: str
    humidity: str
    vibration: str


@app.post("/sensor")
async def receive_data(data: SensorData):
    global latest_reading
    latest_reading = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "vibration": data.vibration,
        "timestamp": time.time()
    }
    return latest_reading


@app.get("/sensor")
async def get_data():
    """
    {
        "temperature": "string",
        "humidity": "string",
        "vibration": "string",
        "timestamp": 0.0
    }

    Use websockets for pulling real-time sensor readings instead of this HTTP GET endpoint:

    ws://domain-name/ws/sensor
    """
    return latest_reading


@app.websocket("/ws/sensor")
async def sensor_socket(websocket: WebSocket):
    await websocket.accept()
    last_timestamp = None
    while True:
        if latest_reading["timestamp"] != last_timestamp:
            await websocket.send_json(latest_reading)
            last_timestamp = latest_reading["timestamp"]
        await asyncio.sleep(1)


handler = Mangum(app)