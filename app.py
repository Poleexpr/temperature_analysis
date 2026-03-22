import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import utils


st.title("Анализ температурных данных и мониторинг текущей температуры")


uploaded_file = st.file_uploader("Загрузите CSV файл", type=["csv"])
if uploaded_file is None:
    st.stop()
df = pd.read_csv(uploaded_file, parse_dates=["timestamp"])


cities = df["city"].unique()
city = st.selectbox("Выберите город", cities)
df = df.sort_values(["city", "timestamp"])
df_city = df[df["city"] == city].copy()


df_city["moving_avg"] = utils.moving_avg(df_city)
avg_and_var = utils.avg_and_var(df_city)
df_city = df_city.join(avg_and_var, on="season")
df_city["is_anomaly"] = utils.anomalies(df_city)


st.subheader("Описательная статистика")
st.write(df_city["temperature"].describe()[["mean", "min", "max"]])
fig0, ax0 = plt.subplots()
ax0.bar(df_city["temperature"].describe()[["mean", "min", "max"]].index, df_city["temperature"].describe()[["mean", "min", "max"]].values)
ax0.set_title("Temperature Statistics")
ax0.set_ylabel("°C")
st.pyplot(fig0)


st.subheader("Температура и аномалии")
min_date = df_city["timestamp"].min()
max_date = df_city["timestamp"].max()
date_range = st.slider(
    "Выберите диапазон дат",
    min_value=min_date.to_pydatetime(),
    max_value=max_date.to_pydatetime(),
    value=(min_date.to_pydatetime(), max_date.to_pydatetime())
)
df_filtered = df_city[
    (df_city["timestamp"] >= date_range[0]) &
    (df_city["timestamp"] <= date_range[1])
]
fig, ax = plt.subplots()
ax.plot(df_filtered["timestamp"], df_filtered["temperature"], label="Температура")
ax.plot(df_filtered["timestamp"], df_filtered["moving_avg"], label="MA")
anomalies_filtered = df_filtered[df_filtered["is_anomaly"]]
ax.scatter(anomalies_filtered["timestamp"], anomalies_filtered["temperature"], label="Аномалии")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
plt.xticks(rotation=45)
ax.legend()
st.pyplot(fig)


st.subheader("Сезонные профили")
fig2, ax2 = plt.subplots()
avg_and_var["mean"].plot(kind="bar", yerr=avg_and_var["std"], ax=ax2)
ax2.set_ylabel("Температура")
st.pyplot(fig2)


st.subheader("Сравнение городов")
selected_cities = st.multiselect("Сравнить города", cities, default=[city])
fig3, ax3 = plt.subplots()
for selected_city in selected_cities:
    temp_df = df[df["city"] == selected_city]
    ax3.plot(temp_df["timestamp"], temp_df["temperature"], label=selected_city)
ax3.legend()
st.pyplot(fig3)


st.subheader("Текущая погода")
api_key = st.text_input("Введите API ключ", type="password")
if api_key:
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"
    }
    response = requests.get(url, params=params)
    data = response.json()
    if "cod" in data and data["cod"] == 401:
        st.error("Invalid API key. Please see https://openweathermap.org/faq#error401 for more info.")
    else:
        current_temp = data["main"]["temp"]
        season = utils.get_season(datetime.now().month)
        if season in avg_and_var.index:
            mean = avg_and_var.loc[season, "mean"]
            std = avg_and_var.loc[season, "std"]
            lower = mean - 2 * std
            upper = mean + 2 * std
            is_anomaly = current_temp < lower or current_temp > upper
            st.write(f"Текущая температура: {current_temp} °C")
            st.write(f"Сезон: {season}")
            st.write(f"Нормальный диапазон: {lower:.2f} — {upper:.2f}")

            if is_anomaly:
                st.error("Температура аномальная")
            else:
                st.success("Температура в норме")
        else:
            st.warning("Нет данных для этого сезона")
else:
    st.info("Введите API ключ, чтобы получить текущую температуру")