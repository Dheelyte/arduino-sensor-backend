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
        - Recommended moisture content of crop: {recommended_moisture_content} %
        - Dryer Type: {dryer}
        - Optimal Air Temperature Range: {optimal_temp_range}°C
        - Optimal Air Velocity Range: {optimal_velocity_range} m/s
        - Typical Drying Time Range: {optimal_drying_time_range} hours
        - Critical Temperature: {critical_temp}°C
        - Notes: Avoid overheating to maintain flavour

        Here are the live readings:
        - Temperature: {temperature}°C
        - Relative Humidity: {humidity}%
        - Air Velocity: {vibration} m/s
        - Drying Time Elapsed: {drying_time_elapsed} hours

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

    context = {
        "optimal_temp_range": "55 - 65",
        "optimal_velocity_range": "1 - 2",
        "optimal_drying_time_range": "6 - 10",
        "critical_temp": "70",
        "recommended_moisture_content": "10 - 20"
    }

    try:
        print(live_sensor_data)
        drying_time_elapsed = (datetime.now(timezone.utc) - live_sensor_data["timestamp"]) / 3600
        result = chain.invoke({
            # "live_sensor_data": live_sensor_data,
            # "optimize": optimize,
            # "context": context,
            "drying_time_elapsed": drying_time_elapsed,
            "temperature": live_sensor_data["temperature"],
            "humidity": live_sensor_data["humidity"],
            "vibration": live_sensor_data["vibration"],
            "crop": optimize.crop,
            "initial_moisture_content": optimize.initial_moisture_content,
            "final_moisture_content": optimize.final_moisture_content,
            "dryer": optimize.dryer,
            "optimal_temp_range": "55 - 65",
            "optimal_velocity_range": "1 - 2",
            "optimal_drying_time_range": "6 - 10",
            "critical_temp": "70",
            "recommended_moisture_content": "10 - 20"
        })
        return result
    except Exception as e:
        print(f"Analysis error: {e}")
        return OptimizationResponse(
            recommendations=["An error occured during optimization"]
        )