#!/usr/bin/env python3
import datetime
import logging

import httpx

# retrieve the weather from the openweather api
async def get_weather(api_key, lat, lon):
    exclude = "minutely,hourly,alerts"
    # TODO add configurable units
    units = "imperial"
    URL = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&units={units}&appid={api_key}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(URL)
            if response.status_code != 200:
                logging.error(
                    f"Failed to get weather info: {response}, api_key = {api_key}, lat = {lat}, lon = {lon}"
                )
                return None
            return response.json()
    except Exception as e:
        logging.error(
            f"Failed to get weather info with exception {e}"
        )
        return None



# takes the weather data and maps it to the corresponding glyph in the weather icon font
# assumes weather data is not none
def to_icon(weather_data):
    icon_id_to_font_code = {"01d": "A",
                            "01n": "B",
                            "02d": "C",
                            "02n": "D",
                            "03d": "E",
                            "03n": "E",
                            "04d": "E",
                            "04n": "E",
                            "09d": "F",
                            "09n": "F",
                            "10d": "G",
                            "10n": "H",
                            "11d": "I",
                            "11n": "I",
                            "13d": "J",
                            "13n": "J",
                            "50d": "K",
                            "50n": "K",
                            }

    weather = weather_data["weather"][0]
    icon_id = weather["icon"]
    return icon_id_to_font_code.get(icon_id)


# assumes weather data is not none
def to_temp(weather_data):
    temp = weather_data["main"]["temp"]
    temp_str = str(int(temp))
    temp_str = temp_str.rjust(2)
    return temp_str


# assumes weather data is not none
def to_sunrise(weather_data):
    sunrise_time = datetime.datetime.fromtimestamp(weather_data["sys"]["sunrise"])
    return sunrise_time

# assumes weather data is not none
def to_sunset(weather_data):
    sunset_time = datetime.datetime.fromtimestamp(weather_data["sys"]["sunset"])
    return sunset_time
