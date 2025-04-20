import requests
from flask import current_app
import logging

def get_weather_data(location):
    """
    Fetch weather data for a given location
    
    Args:
        location (str): City, Country (e.g., "London, UK")
        
    Returns:
        dict: Weather data including temperature, condition, etc. or None if failed
    """
    api_key = current_app.config.get('WEATHER_API_KEY')
    
    # If no API key is configured, return mock data for development
    if not api_key:
        logging.warning("No weather API key configured, returning mock data")
        return {
            'location': location,
            'temperature': 22.5,
            'condition': 'Partly cloudy',
            'humidity': 65,
            'wind_speed': 10,
            'is_raining': False,
            'icon': 'partly-cloudy'
        }
    
    try:
        # Using OpenWeatherMap API (you can replace with any weather API)
        base_url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': location,
            'appid': api_key,
            'units': 'metric'  # for temperature in Celsius
        }
        
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        # Check if we have valid data
        if 'main' not in data or 'weather' not in data:
            logging.error(f"Invalid weather data received for {location}")
            return None
        
        # Extract and format relevant weather information
        weather_data = {
            'location': location,
            'temperature': data['main']['temp'],
            'condition': data['weather'][0]['main'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
            'wind_speed': data['wind']['speed'],
            'is_raining': data['weather'][0]['main'].lower() in ['rain', 'drizzle', 'thunderstorm'],
            'icon': data['weather'][0]['icon']
        }
        
        return weather_data
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching weather data: {e}")
        return None
    except (KeyError, ValueError) as e:
        logging.error(f"Error parsing weather data: {e}")
        return None 