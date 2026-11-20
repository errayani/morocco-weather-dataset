import os
from datetime import datetime, timezone
import pandas as pd
import requests

CITIES = [
    {"city": "Rabat", "city_ar": "الرباط", "region": "Rabat-Salé-Kénitra", "lat": 34.0209, "lon": -6.8416},
    {"city": "Casablanca", "city_ar": "الدار البيضاء", "region": "Casablanca-Settat", "lat": 33.5731, "lon": -7.5898},
    {"city": "Fes", "city_ar": "فاس", "region": "Fès-Meknès", "lat": 34.0331, "lon": -5.0003},
    {"city": "Marrakech", "city_ar": "مراكش", "region": "Marrakech-Safi", "lat": 31.6295, "lon": -7.9811},
    {"city": "Tangier", "city_ar": "طنجة", "region": "Tanger-Tétouan-Al Hoceïma", "lat": 35.7595, "lon": -5.8340},
    {"city": "Agadir", "city_ar": "أكادير", "region": "Souss-Massa", "lat": 30.4278, "lon": -9.5981},
    {"city": "Oujda", "city_ar": "وجدة", "region": "Oriental", "lat": 34.6814, "lon": -1.9086},
    {"city": "Laayoune", "city_ar": "العيون", "region": "Laâyoune-Sakia El Hamra", "lat": 27.1536, "lon": -13.2033},
    {"city": "Dakhla", "city_ar": "الداخلة", "region": "Dakhla-Oued Ed-Dahab", "lat": 23.6848, "lon": -15.9570},
    {"city": "Meknes", "city_ar": "مكناس", "region": "Fès-Meknès", "lat": 33.8935, "lon": -5.5473},
    {"city": "Kenitra", "city_ar": "القنيطرة", "region": "Rabat-Salé-Kénitra", "lat": 34.2610, "lon": -6.5802},
    {"city": "Tetouan", "city_ar": "تطوان", "region": "Tanger-Tétouan-Al Hoceïma", "lat": 35.5889, "lon": -5.3626},
    {"city": "Safi", "city_ar": "آسفي", "region": "Marrakech-Safi", "lat": 32.2994, "lon": -9.2372},
    {"city": "El Jadida", "city_ar": "الجديدة", "region": "Casablanca-Settat", "lat": 33.2316, "lon": -8.5007},
    {"city": "Nador", "city_ar": "الناظور", "region": "Oriental", "lat": 35.1681, "lon": -2.9335},
    {"city": "Beni Mellal", "city_ar": "بني ملال", "region": "Béni Mellal-Khénifra", "lat": 32.3373, "lon": -6.3498},
    {"city": "Errachidia", "city_ar": "الرشيدية", "region": "Drâa-Tafilalet", "lat": 31.9314, "lon": -4.4244},
    {"city": "Guelmim", "city_ar": "كلميم", "region": "Guelmim-Oued Noun", "lat": 28.9870, "lon": -10.0574},
]

WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}

API_URL = "https://api.open-meteo.com/v1/forecast"
OUTPUT_CSV = "morocco_weather.csv"
ARCHIVE_CSV = "data/morocco_weather_history.csv"


def fetch_city_weather(city_info: dict, fetched_at: str) -> list[dict]:
    params = {
        "latitude": city_info["lat"],
        "longitude": city_info["lon"],
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "precipitation_sum",
            "rain_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "uv_index_max",
        ],
        "timezone": "Africa/Casablanca",
        "past_days": 1,
        "forecast_days": 7,
    }
    response = requests.get(API_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()
    daily = payload.get("daily", {})
    dates = daily.get("time", [])

    rows = []
    for i, date_str in enumerate(dates):
        code = daily["weather_code"][i]
        rows.append(
            {
                "date": date_str,
                "city": city_info["city"],
                "city_ar": city_info["city_ar"],
                "region": city_info["region"],
                "latitude": city_info["lat"],
                "longitude": city_info["lon"],
                "weather_code": code,
                "weather_condition": WMO_CODES.get(code, "Unknown"),
                "temp_max_c": daily["temperature_2m_max"][i],
                "temp_min_c": daily["temperature_2m_min"][i],
                "apparent_temp_max_c": daily["apparent_temperature_max"][i],
                "apparent_temp_min_c": daily["apparent_temperature_min"][i],
                "precipitation_mm": daily["precipitation_sum"][i],
                "rain_mm": daily["rain_sum"][i],
                "precip_prob_max_pct": daily["precipitation_probability_max"][i],
                "wind_speed_max_kmh": daily["wind_speed_10m_max"][i],
                "wind_gusts_max_kmh": daily["wind_gusts_10m_max"][i],
                "uv_index_max": daily["uv_index_max"][i],
                "updated_at_utc": fetched_at,
            }
        )
    return rows


def main() -> None:
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    all_rows: list[dict] = []

    for city_info in CITIES:
        all_rows.extend(fetch_city_weather(city_info, fetched_at))

    new_df = pd.DataFrame(all_rows)

    os.makedirs("data", exist_ok=True)
    if os.path.exists(ARCHIVE_CSV):
        existing_df = pd.read_csv(ARCHIVE_CSV)
        combined_df = pd.concat([existing_df, new_df], ignore_index=True)
    else:
        combined_df = new_df

    # إزالة التكرار بناءً على التاريخ والمدينة مع الاحتفاظ بآخر تحديث
    combined_df = combined_df.drop_duplicates(subset=["date", "city"], keep="last")
    combined_df = combined_df.sort_values(["date", "city"]).reset_index(drop=True)

    combined_df.to_csv(ARCHIVE_CSV, index=False)
    combined_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Successfully updated {OUTPUT_CSV} with {len(combined_df)} total rows.")


if __name__ == "__main__":
    main()
