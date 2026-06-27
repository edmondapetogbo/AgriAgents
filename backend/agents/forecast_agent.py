import os
import json
import argparse
from typing import Dict, Any, Optional

from backend.mcp.weather_tool import get_weather

class ForecastAgent:
    def __init__(self):
        """
        Initializes the Forecast Agent.
        """
        pass

    def forecast_risk(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Estimates the disease spread risk based on weather conditions and current disease impact.
        
        Args:
            input_data: Output dictionary from the Diagnosis Agent with an added 'location' field.
                        {
                            "crop": "Tomato",
                            "disease": "Early Blight",
                            "confidence": 97.2,
                            "affected_area_percent": 23.7,
                            "location": "Ahmedabad"
                        }
                        
        Returns:
            Dict: Forecast JSON payload containing spread risk, risk score, weather summary, and reason.
        """
        # Validate inputs
        location = input_data.get("location")
        if not location:
            raise ValueError("Input data must contain a 'location' field.")
            
        affected_area_percent = input_data.get("affected_area_percent")
        if affected_area_percent is None:
            raise ValueError("Input data must contain an 'affected_area_percent' field.")
            
        # 1. Retrieve weather data from Weather Tool
        weather = get_weather(location=location)
        
        temperature = weather["temperature"]
        humidity = weather["humidity"]
        rain_probability = weather["rain_probability"]
        
        # 2. Run Rule-Based Risk Engine
        score = 0
        
        # Humidity Rule
        if humidity > 80:
            score += 35
        elif 60 <= humidity <= 80:
            score += 20
        else:
            score += 5
            
        # Rain Probability Rule
        if rain_probability > 60:
            score += 30
        elif 30 <= rain_probability <= 60:
            score += 15
        else:
            score += 5
            
        # Temperature Rule
        if 20 <= temperature <= 30:
            score += 20
        else:
            score += 10
            
        # Affected Area Rule
        if affected_area_percent > 50:
            score += 20
        elif 20 <= affected_area_percent <= 50:
            score += 10
        else:
            score += 5
            
        # Clamp score to 100
        score = min(100, max(0, score))
        
        # Determine risk level
        if score <= 39:
            spread_risk = "Low"
            reason = "Low humidity, low rain probability, or suboptimal temperatures limit the spread of the pathogen."
        elif score <= 69:
            spread_risk = "Medium"
            reason = "Moderate weather conditions and existing leaf damage pose a medium risk of disease spread."
            # High humidity or rain could also trigger specific explanations
            if humidity > 80 or rain_probability > 60:
                reason = "High humidity and rainfall increase fungal disease spread."
        else:
            spread_risk = "High"
            reason = "High humidity, rainfall, and optimal temperatures heavily accelerate pathogen spread across damaged leaves."
            
        # 3. Build output structure
        return {
            "spread_risk": spread_risk,
            "risk_score": score,
            "weather_summary": {
                "temperature": int(round(temperature)),
                "humidity": int(humidity),
                "rain_probability": int(rain_probability)
            },
            "reason": reason
        }

def main():
    parser = argparse.ArgumentParser(description="Estimate disease spread risk based on diagnosis and weather")
    parser.add_argument("--location", type=str, required=True, help="City location for weather data")
    parser.add_argument("--crop", type=str, default="Tomato", help="Crop name")
    parser.add_argument("--disease", type=str, default="Early Blight", help="Detected disease name")
    parser.add_argument("--confidence", type=float, default=95.0, help="Classifier confidence percent")
    parser.add_argument("--affected_area", type=float, required=True, help="Affected leaf area percentage")
    args = parser.parse_args()
    
    input_data = {
        "crop": args.crop,
        "disease": args.disease,
        "confidence": args.confidence,
        "affected_area_percent": args.affected_area,
        "location": args.location
    }
    
    try:
        agent = ForecastAgent()
        result = agent.forecast_risk(input_data)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
