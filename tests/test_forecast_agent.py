import unittest
from unittest.mock import patch, MagicMock

from backend.agents.forecast_agent import ForecastAgent

class TestForecastAgent(unittest.TestCase):

    def setUp(self):
        self.agent = ForecastAgent()

    @patch("backend.agents.forecast_agent.get_weather")
    def test_low_risk_scenario(self, mock_get_weather):
        """
        Verify risk score calculations under low spread risk conditions.
        """
        # Mock weather showing cool, dry, no-rain parameters
        mock_get_weather.return_value = {
            "temperature": 15.0,  # +10 (outside 20-30)
            "humidity": 45,       # +5  (<60)
            "rain_probability": 10 # +5  (<30)
        }
        
        input_data = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 90.0,
            "affected_area_percent": 10.0,  # +5 (<20)
            "location": "Ahmedabad"
        }
        
        result = self.agent.forecast_risk(input_data)
        
        # Expected score: 10 + 5 + 5 + 5 = 25
        self.assertEqual(result["risk_score"], 25)
        self.assertEqual(result["spread_risk"], "Low")
        self.assertEqual(result["weather_summary"]["temperature"], 15)
        self.assertEqual(result["weather_summary"]["humidity"], 45)
        self.assertEqual(result["weather_summary"]["rain_probability"], 10)

    @patch("backend.agents.forecast_agent.get_weather")
    def test_medium_risk_scenario(self, mock_get_weather):
        """
        Verify risk score calculations under moderate weather/impact conditions.
        """
        # Mock weather showing warm, moderate humidity/rain conditions
        mock_get_weather.return_value = {
            "temperature": 25.0,  # +20 (in 20-30)
            "humidity": 70,       # +20 (60-80)
            "rain_probability": 40 # +15 (30-60)
        }
        
        input_data = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 95.0,
            "affected_area_percent": 30.0,  # +10 (20-50)
            "location": "Ahmedabad"
        }
        
        result = self.agent.forecast_risk(input_data)
        
        # Expected score: 20 + 20 + 15 + 10 = 65
        self.assertEqual(result["risk_score"], 65)
        self.assertEqual(result["spread_risk"], "Medium")

    @patch("backend.agents.forecast_agent.get_weather")
    def test_high_risk_scenario_clamped(self, mock_get_weather):
        """
        Verify risk score calculations under severe conditions, checking clamping bounds.
        """
        # Mock weather showing warm, humid, heavy rain conditions
        mock_get_weather.return_value = {
            "temperature": 28.0,  # +20 (in 20-30)
            "humidity": 85,       # +35 (>80)
            "rain_probability": 75 # +30 (>60)
        }
        
        input_data = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 97.2,
            "affected_area_percent": 55.0,  # +20 (>50)
            "location": "Ahmedabad"
        }
        
        result = self.agent.forecast_risk(input_data)
        
        # Expected raw score: 20 + 35 + 30 + 20 = 105
        # Clamped score: 100
        self.assertEqual(result["risk_score"], 100)
        self.assertEqual(result["spread_risk"], "High")

    def test_missing_location(self):
        """
        Verify that a ValueError is raised when location is missing.
        """
        input_data = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 90.0,
            "affected_area_percent": 15.0
            # Missing location
        }
        
        with self.assertRaises(ValueError) as context:
            self.agent.forecast_risk(input_data)
            
        self.assertIn("location", str(context.exception))

    @patch("backend.agents.forecast_agent.get_weather")
    def test_weather_api_failure(self, mock_get_weather):
        """
        Verify that weather API network exceptions propagate up correctly.
        """
        # Make weather tool throw a connection refusal exception
        mock_get_weather.side_effect = Exception("API connection timed out")
        
        input_data = {
            "crop": "Tomato",
            "disease": "Early Blight",
            "confidence": 90.0,
            "affected_area_percent": 15.0,
            "location": "Ahmedabad"
        }
        
        with self.assertRaises(Exception) as context:
            self.agent.forecast_risk(input_data)
            
        self.assertIn("API connection timed out", str(context.exception))

if __name__ == "__main__":
    unittest.main()
