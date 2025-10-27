from datetime import datetime
from pydantic import BaseModel


class OptimizationRequest(BaseModel):
    dryer: str
    crop: str
    initial_moisture_content: str
    final_moisture_content: str
    timestamp: datetime


class OptimizationResponse(BaseModel):
    recommendations: list[str]
    estimated_moisture_content: str
    optimal_drying_time_range: str


class SensorData(BaseModel):
    temperature: str
    humidity: str
    vibration: str
    timestamp: datetime