import requests
import random
import time
from datetime import datetime, timezone

# Replace with your target endpoint
ENDPOINT = "https://bipel2bpd2pgq3ojogco5nujky0icbnh.lambda-url.eu-north-1.on.aws/api/sensor"  

def generate_random_data():
    """Generate random sensor data."""
    return {
        "temperature": str(random.randint(20, 100)),  # °C
        "humidity": str(random.randint(10, 90)),     # %
        "vibration": str(random.randint(0, 50)),     # arbitrary unit
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def send_data():
    """Send random JSON data to the endpoint repeatedly."""
    while True:
        data = generate_random_data()
        try:
            response = requests.post(ENDPOINT, json=data)
            print(f"Sent: {data} | Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending data: {e}")
        time.sleep(2)  # wait 2 seconds before sending next data

if __name__ == "__main__":
    send_data()
