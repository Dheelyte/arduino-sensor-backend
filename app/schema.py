from enum import Enum
from datetime import datetime
from pydantic import BaseModel


class OptimizationRequest(BaseModel):
    dryer: str
    crop: str
    initial_moisture_content: str
    final_moisture_content: str
    timestamp: datetime


class RecommendationLevel(str, Enum):
    DANGER = "danger"
    WARNING = "warning"
    OPTIMAL = "optimal"


class OptimizationResponse(BaseModel):
    recommendations: list[tuple[RecommendationLevel, str]]
    estimated_moisture_content: str
    drying_time_elapsed: str
    drying_time_hours: str


class SensorData(BaseModel):
    temperature: str
    humidity: str
    vibration: str
    timestamp: datetime