import unittest
from unittest.mock import patch, MagicMock
import urllib.request
import urllib.error
import json

from backend.mcp.weather_tool import get_weather, geocode_city

class MockResponse:
    def __init__(self, data_dict: dict, status: int = 200):
        self.data = json.dumps(data_dict).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self.data

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def mock_urlopen_side_effect(req, *args, **kwargs):
    # Extract url string
    if isinstance(req, urllib.request.Request):
        url = req.full_url
    else:
        url = req

    # Geocoding API mock responses
    if "geocoding-api.open-meteo.com" in url:
        if "invalid" in url.lower():
            # Return empty results for invalid city
            return MockResponse({"results": []})
        return MockResponse({
            "results": [
                {
                    "name": "Ahmedabad",
                    "latitude": 23.02579,
                    "longitude": 72.57737
                }
            ]
        })

    # Weather Forecast API mock responses
    if "api.open-meteo.com" in url:
        return MockResponse({
            "current": {
                "time": "2026-06-27T12:00",
                "temperature_2m": 29.4,
                "relative_humidity_2m": 82
            },
            "hourly": {
                "time": ["2026-06-27T11:00", "2026-06-27T12:00", "2026-06-27T13:00"],
                "precipitation_probability": [40, 67, 10]
            }
        })

    return MockResponse({}, status=404)

class TestWeatherTool(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_valid_city_weather(self, mock_urlopen):
        """
        Verify that querying weather for a valid city returns coordinates,
        performs successful geocoding, and retrieves hourly precipitation probability matched by time.
        """
        mock_urlopen.side_effect = mock_urlopen_side_effect
        
        # Request weather for a valid city
        result = get_weather(location="Ahmedabad")
        
        self.assertIn("temperature", result)
        self.assertIn("humidity", result)
        self.assertIn("rain_probability", result)
        
        self.assertEqual(result["temperature"], 29.4)
        self.assertEqual(result["humidity"], 82)
        self.assertEqual(result["rain_probability"], 67)

    @patch("urllib.request.urlopen")
    def test_invalid_city_weather(self, mock_urlopen):
        """
        Verify that geocoding an invalid city raises a ValueError.
        """
        mock_urlopen.side_effect = mock_urlopen_side_effect
        
        # Querying an invalid city name should raise a ValueError
        with self.assertRaises(ValueError) as context:
            get_weather(location="InvalidCityName")
            
        self.assertIn("could not be resolved", str(context.exception))

    @patch("urllib.request.urlopen")
    def test_coordinates_weather(self, mock_urlopen):
        """
        Verify that querying weather using direct coordinates skips geocoding
        and retrieves values correctly.
        """
        mock_urlopen.side_effect = mock_urlopen_side_effect
        
        result = get_weather(latitude=23.02, longitude=72.57)
        
        self.assertEqual(result["temperature"], 29.4)
        self.assertEqual(result["humidity"], 82)
        self.assertEqual(result["rain_probability"], 67)

    @patch("urllib.request.urlopen")
    @patch("time.sleep") # speed up tests by mocking retry sleep delay
    def test_api_unavailable_with_retry(self, mock_sleep, mock_urlopen):
        """
        Verify that the HTTP client retries once on network failure before raising an error.
        """
        # Make the request raise URLError
        mock_urlopen.side_effect = urllib.error.URLError("Connection timed out")
        
        with self.assertRaises(urllib.error.URLError):
            get_weather(location="Ahmedabad", retries=1)
            
        # Verify urlopen was called twice (1 initial + 1 retry)
        self.assertEqual(mock_urlopen.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)

if __name__ == "__main__":
    unittest.main()
