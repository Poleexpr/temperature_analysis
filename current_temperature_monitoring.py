import pandas as pd
import requests
import aiohttp
import asyncio
from datetime import datetime
import time
from utils import get_season, avg_and_var
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("WEATHER_API_KEY")


def get_current_temp_sync(city):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    response = requests.get(url, params=params)
    data = response.json()

    return data["main"]["temp"]


async def get_current_temp_async(session, city):
    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    async with session.get(url, params=params) as response:
        data = await response.json()
        return city, data["main"]["temp"]


async def get_all_temps(cities):
    async with aiohttp.ClientSession() as session:
        tasks = [get_current_temp_async(session, city) for city in cities]
        return await asyncio.gather(*tasks)


def anomalies_current(city, current_temp, avg_and_var):
    month = datetime.now().month
    season = get_season(month)
    mean = avg_and_var.loc[(city, season), "mean"]
    std = avg_and_var.loc[(city, season), "std"]
    lower = mean - 2 * std
    upper = mean + 2 * std
    is_anomaly = current_temp < lower or current_temp > upper
    return {
        "city": city,
        "season": season,
        "is_anomaly": is_anomaly
    }


def fetch_sync(cities, avg_and_var):
    results = []
    for city in cities:
        temp = get_current_temp_sync(city)
        r = anomalies_current(city, temp, avg_and_var)
        results.append(r)
        print(r)
    return results

async def fetch_async(cities, avg_and_var):
    temps = await get_all_temps(cities)
    results = []
    for city, temp in temps:
        r = anomalies_current(city, temp, avg_and_var)
        results.append(r)
        print(r)
    return results

if __name__ == "__main__":
    df = pd.read_csv("temperature_data.csv", parse_dates=["timestamp"])
    df = df.sort_values(["city", "timestamp"])
    avg_and_var = avg_and_var(df, ["city", "season"])
    cities = ["Berlin", "Cairo", "Dubai", "Beijing", "Moscow"]

    start = time.time()
    sync_results = fetch_sync(cities, avg_and_var)
    sync_time = time.time() - start

    start = time.time()
    async_results = asyncio.run(fetch_async(cities, avg_and_var))
    async_time = time.time() - start

    print(f"Синхронно:   {sync_time:.4f} s")
    print(f"Асинхронно:  {async_time:.4f} s")


    # Асинхронный подход быстрее, потому что он прекрано подходит для выполнения I/O-boun задач, к которым относятся запрсы к API. При синхронном подходе приходится ждать окончания каждого запроса, в то время как при асинхронном возможно переключение между задачами