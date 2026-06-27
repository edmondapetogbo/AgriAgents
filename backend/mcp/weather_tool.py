import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
import argparse
from typing import Dict, Any, Optional

def _fetch_json_with_retry(url: str, timeout: float = 10.0, retries: int = 1) -> Dict[str, Any]:
    """
    Fetches JSON data from a URL with a timeout and retry mechanism.
    
    Args:
        url: The API endpoint URL to fetch.
        timeout: Timeout in seconds for the network request.
        retries: Number of retry attempts if the request fails or times out.
        
    Returns:
        Dict[str, Any]: The parsed JSON response.
    """
    last_error: Optional[Exception] = None
    
    for attempt in range(retries + 1):
        try:
            # Custom User-Agent to conform to Open-Meteo's guidelines
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "AgriAgents/1.0 (contact: github.com/edmondapetogbo/AgriAgents)"}
            )
            
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.status
                if status == 200:
                    data = response.read().decode("utf-8")
                    return json.loads(data)
                else:
                    raise urllib.error.HTTPError(
                        url, status, f"HTTP Error {status}", response.headers, None
                    )
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last_error = e
            if attempt < retries:
                # Wait 1 second before retrying
                time.sleep(1.0)
                continue
                
    if last_error:
        raise last_error
    raise Exception("Unknown error occurred during fetch.")

def geocode_city(city_name: str, timeout: float = 10.0, retries: int = 1) -> tuple[float, float]:
    """
    Geocodes a city name into latitude and longitude using Open-Meteo Geocoding API.
    
    Args:
        city_name: Name of the city to geocode.
        timeout: Timeout in seconds for the network request.
        retries: Number of retry attempts.
        
    Returns:
        tuple[float, float]: Latitude and Longitude.
    """
    encoded_city = urllib.parse.quote(city_name.strip())
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={encoded_city}&count=1&format=json"
    
    response = _fetch_json_with_retry(url, timeout=timeout, retries=retries)
        
    results = response.get("results")
    if not results or len(results) == 0:
        raise ValueError(f"Location '{city_name}' could not be resolved.")
        
    location_data = results[0]
    return float(location_data["latitude"]), float(location_data["longitude"])

def get_weather(
    location: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    timeout: float = 10.0,
    retries: int = 1
) -> Dict[str, Any]:
    """
    Retrieves temperature, relative humidity, and rain probability using Open-Meteo API.
    
    Args:
        location: Optional city name. If provided, it is geocoded first.
        latitude: Optional latitude coordinate.
        longitude: Optional longitude coordinate.
        timeout: Timeout in seconds for the network requests.
        retries: Number of retry attempts.
        
    Returns:
        Dict[str, Any]: Normalized dictionary:
        {
            "temperature": 29.4,
            "humidity": 82,
            "rain_probability": 67
        }
    """
    if location:
        # Geocode the city first
        lat, lon = geocode_city(location, timeout=timeout, retries=retries)
    elif latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        raise ValueError("Must provide either a 'location' or both 'latitude' and 'longitude'.")
        
    # Construct forecast query
    # current: temperature_2m, relative_humidity_2m
    # hourly: precipitation_probability
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m"
        f"&hourly=precipitation_probability"
    )
    
    response = _fetch_json_with_retry(url, timeout=timeout, retries=retries)
        
    # Extract values
    current = response.get("current")
    hourly = response.get("hourly")
    
    if not current or not hourly:
        raise ValueError("Failed to retrieve current or hourly forecast data from API response.")
        
    temperature = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    
    if temperature is None or humidity is None:
        raise ValueError("Current temperature or humidity is missing in API response.")
        
    # Extract rain probability matching current observation hour
    current_time_str = current.get("time")
    rain_probability = 0
    
    if current_time_str and "time" in hourly and "precipitation_probability" in hourly:
        try:
            times = hourly["time"]
            probs = hourly["precipitation_probability"]
            if current_time_str in times:
                idx = times.index(current_time_str)
                rain_probability = probs[idx]
            else:
                # If exact time is not found, fallback to the first hourly prediction
                rain_probability = probs[0] if len(probs) > 0 else 0
        except (ValueError, IndexError):
            pass
            
    return {
        "temperature": float(temperature),
        "humidity": int(humidity),
        "rain_probability": int(rain_probability)
    }

def main():
    parser = argparse.ArgumentParser(description="Query weather conditions from Open-Meteo API")
    parser.add_argument("--location", type=str, help="Location/City name")
    parser.add_argument("--latitude", type=float, help="Latitude coordinate")
    parser.add_argument("--longitude", type=float, help="Longitude coordinate")
    args = parser.parse_args()
    
    try:
        weather = get_weather(
            location=args.location,
            latitude=args.latitude,
            longitude=args.longitude
        )
        print(json.dumps(weather, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=2))

if __name__ == "__main__":
    main()
