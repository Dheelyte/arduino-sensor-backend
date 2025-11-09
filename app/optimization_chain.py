import json, os
from datetime import datetime, timezone
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.config import load_google_llm
from app.schema import OptimizationRequest, OptimizationResponse, SensorData


def create_analysis_chain():
    llm = load_google_llm()
    parser = PydanticOutputParser(pydantic_object=OptimizationResponse)
    format_instructions = parser.get_format_instructions()

    system_message = """
        You are an agricultural drying optimization assistant.

        Based on these live readings and optimal conditions, provide:
        - 5 actionable optimization tips to improve drying efficiency, avoid spoilage, and maintain product quality. 
        - The estimated moisture content value ONLY.
        - The optimal drying time range"""

    user_template = """Here's the drying setup:
        - Crop: {crop}
        - Initial moisture content of crop: {initial_moisture_content}
        - Target moisture content of crop: {final_moisture_content}
        - Recommended target moisture content of crop: {final_moisture_content} %
        - Dryer Type: {dryer_type}
        - Optimal Air Temperature Range: {air_temp_max}°C
        - Optimal Air Velocity Range: {air_velocity_max} m/s
        - Typical Drying Time Range: {drying_time_hours} hours
        - Critical Temperature: {critical_temp}°C
        - Notes: Avoid overheating to maintain flavour

        Here are the live readings:
        - Temperature: {temperature}°C
        - Relative Humidity: {humidity}%
        - Air Velocity: {vibration} m/s
        - Drying Time Elapsed: {drying_time_elapsed} (Format to hours:minutes:seconds).

        {format_instructions}

        Respond ONLY with valid JSON."""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("user", user_template)
    ])

    prompt = prompt.partial(format_instructions=format_instructions)
    chain = prompt | llm | parser

    return chain


def analyse_optimization(optimize: OptimizationRequest, live_sensor_data: SensorData):
    chain = create_analysis_chain()
    try:
        drying_time_elapsed = datetime.now(timezone.utc) - live_sensor_data["timestamp"]
            
        context = find_crop_dryer(optimize.crop, optimize.dryer)

        result = chain.invoke({
            "drying_time_elapsed": drying_time_elapsed,
            "temperature": live_sensor_data["temperature"],
            "humidity": live_sensor_data["humidity"],
            "vibration": live_sensor_data["vibration"],
            "initial_moisture_content": optimize.initial_moisture_content,
            "final_moisture_content": optimize.final_moisture_content,
            "crop": context["crop"],
            "dryer_type": context["dryer_type"],
            "air_temp_max": context["air_temp_max"],
            "air_velocity_max": context["air_velocity_max"],
            "drying_time_hours": context["drying_time_hours"],
            "critical_temp": context["critical_temp"],
            "final_moisture_content": context["final_moisture_content"]
        })
        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        return OptimizationResponse(
            recommendations=["An error occured during optimization"]
        )
    

import os, json, re

def find_crop_dryer(crop, dryer_type):
    """
    Find drying parameters for a given crop and dryer type
    from the combined OptiDry JSON data.
    """

    json_path = os.path.join(os.path.dirname(__file__), "crop_dryer_data.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    def get_key_value(d, key_pattern):
        """Finds value in dict `d` where key matches the regex pattern (case-insensitive)."""
        for k, v in d.items():
            if re.search(key_pattern, k, re.IGNORECASE):
                return v
        return None

    for entry in data:
        if entry["Crop"].lower() == crop.lower():
            for dryer in entry["Dryers"]:
                if dryer["Dryer Type"].lower() == dryer_type.lower():
                    return {
                        "dryer_type": dryer.get("Dryer Type"),
                        "crop": entry.get("Crop"),
                        "air_temp_max": get_key_value(dryer, r"air\s*temp"),
                        "air_velocity_max": get_key_value(dryer, r"air\s*velocity"),
                        "drying_time_hours": get_key_value(dryer, r"drying\s*time"),
                        "critical_temp": get_key_value(entry, r"critical\s*temp"),
                        "final_moisture_content": get_key_value(entry, r"final\s*mc"),
                    }

    # If not found
    return {
        "dryer_type": dryer_type,
        "crop": crop,
        "air_temp_max": None,
        "air_velocity_max": None,
        "drying_time_hours": None,
        "critical_temp": None,
        "final_moisture_content": None
    }
