import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, WebSocket

from .schema import OptimizationRequest, OptimizationResponse, SensorData
from .optimization_chain import analyse_optimization


router = APIRouter(prefix="/api", tags=["Optimization"])


# # Store last reading in memory
latest_reading = {
    "temperature": None,
    "humidity": None,
    "vibration": None,
    "timestamp": None
}


@router.get("/sensor")
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


@router.post("/sensor")
async def receive_data(data: SensorData):
    global latest_reading
    latest_reading = {
        "temperature": data.temperature,
        "humidity": data.humidity,
        "vibration": data.vibration,
        "timestamp": datetime.now(timezone.utc)
    }
    return latest_reading


@router.websocket("/ws/sensor")
async def sensor_socket(websocket: WebSocket):
    await websocket.accept()
    last_timestamp = None
    while True:
        if latest_reading["timestamp"] != last_timestamp:
            await websocket.send_json(latest_reading)
            last_timestamp = latest_reading["timestamp"]
        await asyncio.sleep(1)


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize(request: OptimizationRequest):
    try:
        optimization = analyse_optimization(request, latest_reading)
        return OptimizationResponse(
            recommendations=optimization.recommendations,
            estimated_moisture_content=optimization.estimated_moisture_content,
            optimal_drying_time_range=optimization.optimal_drying_time_range
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization error: Make sure the sensors are properly connected")
