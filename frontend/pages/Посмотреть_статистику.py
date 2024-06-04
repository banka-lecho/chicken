import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from pages.utils.login import check_password

if not check_password():
    st.stop()

st.title("Статистика по партиям")

st.sidebar.header("Параметры запроса статистики")
start_date = st.date_input("Начало периода", datetime.now() - timedelta(days=1))
end_date = st.date_input("Конец периода", datetime.now())

start_time = st.time_input('Время начала подсчёта')
end_time = st.time_input('Время окончания подсчёта')

start_datetime = datetime.combine(start_date, start_time)
end_datetime = datetime.combine(end_date, end_time)

response = requests.get('http://backend:9032/chickens/')
data = response.json()['chickens']
df = pd.DataFrame(data)
if response.status_code != 200:
    st.write("Не удалось получить данные таблицы Chickens")

if st.button("Получить статистику"):
    start_period_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    end_period_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    response_count = requests.get(
        f'http://backend:9032/count/{str(start_period_iso)}/{str(end_period_iso)}', json={
            'start_period_iso': start_period_iso, 'end_period_iso': end_period_iso})
    data_count = response_count.json()['count']
    st.write(f'Общее количество цыплят за выбранный промежуток времени: {data_count}')
