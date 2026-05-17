import requests

API_KEY = "fffbf69aa5004d2d88b154502260204"

SEASONAL_FALLBACK = {
    "Summer": {"Temperature": 28.0, "Humidity": 80.0, "Rainfall": 12.5},
    "Winter": {"Temperature": 12.0, "Humidity": 55.0, "Rainfall": 1.2},
    "Spring": {"Temperature": 22.0, "Humidity": 60.0, "Rainfall": 4.5},
}

RAIN_ALERT_THRESHOLD = 20  # mm in 48 hours

def get_weather(lat, lon, season=None, application_date=None):
    url = f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={lat},{lon}&days=3&dt={application_date}"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            raise ValueError(f"WeatherAPI returned {res.status_code}")

        data = res.json()
        if "error" in data:
            raise ValueError(data["error"]["message"])

        current  = data.get("current", {})
        forecast = data.get("forecast", {}).get("forecastday", [])

        temp     = current.get("temp_c")
        humidity = current.get("humidity")

        if temp is None or humidity is None:
            raise ValueError("Incomplete weather data")

        # Total rainfall over full forecast period (for ML feature)
        total_rainfall = sum(day["day"]["totalprecip_mm"] for day in forecast)

        # 48-hour rainfall for rain alert (next 2 days only)
        rainfall_48h = sum(
            day["day"]["totalprecip_mm"]
            for day in forecast[:2]
        )

        rain_alert = rainfall_48h > RAIN_ALERT_THRESHOLD

        return {
            "Temperature" : float(temp),
            "Humidity"    : float(humidity),
            "Rainfall"    : float(round(total_rainfall, 2)),
            "Rainfall_48h": float(round(rainfall_48h, 2)),
            "rain_alert"  : rain_alert,
        }

    except Exception as e:
        fallback_key = season if season in SEASONAL_FALLBACK else "Summer"
        fallback     = SEASONAL_FALLBACK[fallback_key]
        print(f"[WeatherAPI] Failed ({e}) - using seasonal fallback for {fallback_key}")
        return {
            **fallback,
            "Rainfall_48h": 0.0,
            "rain_alert"  : False,
            "_fallback"   : True,
        }