import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, WebSocket
from starlette.websockets import WebSocketDisconnect

from .schema import OptimizationRequest, OptimizationResponse, SensorData
from .optimization_chain import analyse_optimization
from fastapi.responses import HTMLResponse
from pathlib import Path


router = APIRouter(tags=["Optimization"])

frontend_connections = set()


# # Store last reading in memory
latest_reading = {
    "temperature": None,
    "humidity": None,
    "vibration": None,
    "timestamp": None
}

@router.get("/frontend", response_class=HTMLResponse)
def get_frontend():
    return Path("tests/frontend.html").read_text()

@router.get("/device", response_class=HTMLResponse)
def get_device():
    return Path("tests/device.html").read_text()


@router.websocket("/ws/sensor")
async def sensor_socket(websocket: WebSocket):
    """Frontend clients connect here to receive live updates"""
    await websocket.accept()
    frontend_connections.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)  # just keep connection alive
    except WebSocketDisconnect:
        frontend_connections.remove(websocket)


@router.websocket("/ws/device")
async def device_socket(websocket: WebSocket):
    """Devices send new readings here"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            latest_reading.update(data)
            # Broadcast to all connected frontend clients
            for client in list(frontend_connections):
                try:
                    await client.send_json(latest_reading)
                except WebSocketDisconnect:
                    frontend_connections.remove(client)
    except WebSocketDisconnect:
        print("Device disconnected")

    
@router.get("/optimize", response_model=OptimizationResponse)
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



# @router.get("/sensor")
# async def get_data():
#     """
#     {
#         "temperature": "string",
#         "humidity": "string",
#         "vibration": "string",
#         "timestamp": 0.0
#     }

#     Use websockets for pulling real-time sensor readings instead of this HTTP GET endpoint:

#     ws://domain-name/ws/sensor
#     """
#     return latest_reading


# @router.post("/sensor")
# async def receive_data(data: SensorData):
#     global latest_reading
#     latest_reading = {
#         "temperature": data.temperature,
#         "humidity": data.humidity,
#         "vibration": data.vibration,
#         "timestamp": datetime.now(timezone.utc)
#     }
#     return latest_reading


# @router.websocket("/ws/sensor")
# async def sensor_socket(websocket: WebSocket):
#     await websocket.accept()
#     last_timestamp = None
#     while True:
#         if latest_reading["timestamp"] != last_timestamp:
#             await websocket.send_json(latest_reading)
#             last_timestamp = latest_reading["timestamp"]
#         await asyncio.sleep(1)


# @router.websocket("/ws/device")
# async def device_socket(websocket: WebSocket):
#     """Devices send new readings here"""
#     await websocket.accept()
#     try:
#         while True:
#             data = await websocket.receive_json()
#             latest_reading.update(data)
#             # Broadcast to all connected frontend clients
#             for client in list(frontend_connections):
#                 try:
#                     await client.send_json(latest_reading)
#                 except WebSocketDisconnect:
#                     frontend_connections.remove(client)
#     except WebSocketDisconnect:
#         print("Device disconnected")


# @router.websocket("/ws/device")
# async def device_ws(websocket: WebSocket):
#     """
#     Handles WebSocket connections from devices.
#     """
#     await handle_device_websocket_service(websocket)

# @router.websocket("/ws/frontend")
# async def frontend_ws(websocket: WebSocket):
#     """
#     Handles WebSocket connections from the frontend.
#     """
#     await handle_frontend_websocket_service(websocket)

# async def handle_device_websocket_service(websocket: WebSocket):
#     """
#     Handles WebSocket connections from devices, manages real-time data forwarding to frontend clients,
#     and conditionally stores incoming data to the database in buffered batches.
#     """
#     await websocket.accept()
#     device_id = websocket.query_params.get("device_id")
#     if not device_id:
#         await websocket.close()
#         return

#     device_connections[device_id] = websocket

#     # print(f"Device {device_id} connected.")

#     try:
#         inserted_id = ""
#         while True:
#             data = await websocket.receive_text()
#             data_point = json.loads(data)

#             # Forward to frontend
#             if device_id in frontend_connections:
#                 for client_ws in frontend_connections[device_id]:
#                     await client_ws.send_text(data)

#             # Store to DB if toggled on
#             if store_reading_flags.get(device_id):
#                 # if not isinstance(data_point, (int, float)): # it slows down the process
#                 # data_point = data_point.get("value")
#                 # if data_point is None:
#                 #     continue

#                 reading_buffers[device_id].append(float(data_point))

#                 # Save when buffer reaches threshold
#                 if len(reading_buffers[device_id]) >= BUFFER_SIZE:
#                     session_id = current_sessions[device_id]
#                     reading_buffers[device_id][:BUFFER_SIZE]

#                     if device_id not in session_docs:
#                         inserted_id = await ReadingRepository.store_reading_with_array({
#                             "device_id": device_id,
#                             "session_id": session_id
#                         }, reading_buffers[device_id][:BUFFER_SIZE])
#                         session_docs[device_id] = inserted_id
#                     else:
#                         await ReadingRepository.append_to_array(inserted_id, reading_buffers[device_id][:BUFFER_SIZE])

#                     reading_buffers[device_id].clear()

#     except WebSocketDisconnect:
#         # print(f"Device {device_id} disconnected.")
#         device_connections.pop(device_id, None)

#         # Handle pending buffer if session was active
#         if store_reading_flags.get(device_id):
#             buffer = reading_buffers.get(device_id, [])
#             if buffer:
#                 session_id = current_sessions.get(device_id)
#                 if device_id not in session_docs:
#                     inserted_id = await ReadingRepository.store_reading_with_array({
#                             "device_id": device_id,
#                             "session_id": session_id
#                         }, buffer)
#                     session_docs[device_id] = inserted_id
#                 else:
#                     await ReadingRepository.append_to_array(session_docs[device_id], buffer)

#             # Clear session state (turn off save)
#             store_reading_flags.pop(device_id, None)
#             current_sessions.pop(device_id, None)
#             reading_buffers.pop(device_id, None)
#             session_docs.pop(device_id, None)


# async def handle_frontend_websocket_service(websocket: WebSocket):
#     """
#     Handles WebSocket connections from the frontend for a specific device.
#     """
#     await websocket.accept()
#     device_id = websocket.query_params.get("device_id")
#     if not device_id:
#         # print("Frontend WebSocket connection denied: Missing device_id.")
#         await websocket.close(code=1008) # Policy Violation
#         return

#     if device_id not in frontend_connections:
#         frontend_connections[device_id] = []

#     if len(frontend_connections[device_id]) >= MAX_NUM_OF_FRONTEND_CONNECTIONS:
#         # print(f"Frontend connection limit reached for device {device_id}. Closing all previous connections.")
#         for conn in frontend_connections[device_id]:
#             # delete it from the list
#             frontend_connections[device_id].remove(conn)