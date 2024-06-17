import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
from pages.utils.login import check_password

if not check_password():
    st.stop()

st.title("Статистика по партиям")
response = requests.get('http://backend:9032/chickens/')
data = response.json()['chickens']
df = pd.DataFrame(data)
st.dataframe(df)

# todo:: сделать проверку на пустоту полей

if df.shape[0] == 0:
    st.write('Таблица с данными о партиях пуста. Добавьте для начала информацию о партиях.')
else:
    action = st.selectbox('Выберете действие:',
                          options=['Посмотреть параметры партии', 'Посмотреть статистику по времени'])

    if action == 'Посмотреть статистику по времени':
        with st.form(key='edit_form'):
            st.sidebar.header("Параметры запроса статистики")
            start_date = st.date_input("Начало периода", datetime.now() - timedelta(days=1))
            end_date = st.date_input("Конец периода", datetime.now())

            start_time = st.time_input('Время начала подсчёта')
            end_time = st.time_input('Время окончания подсчёта')

            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            button = st.form_submit_button("Получить статистику")
            if button:
                start_period_iso = start_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                end_period_iso = end_datetime.strftime("%Y-%m-%dT%H:%M:%S")
                response_count = requests.get(
                    f'http://backend:9032/count/{str(start_period_iso)}/{str(end_period_iso)}', json={
                        'start_period_iso': start_period_iso, 'end_period_iso': end_period_iso})
                data_count = response_count.json()['count']
                st.write(f'Общее количество цыплят за выбранный промежуток времени: {data_count}')

    elif action == 'Посмотреть параметры партии':
        with st.form(key='edit_form'):
            batch_id = st.text_input("Введите номер партии")
            button = st.form_submit_button("Получить статистику")
            if button:
                response_batch = requests.get(f'http://backend:9032/chickens/{str(batch_id)}',
                                              json={'batch_id': batch_id})
                if response.status_code != 200:
                    st.error('Не удалось отправить запрос на получение')
                    st.write(response.status_code)
                    st.write(response.text)

                batch_info = response_batch.json()['batch_info']
                df = pd.DataFrame(batch_info, index=[0])
                st.dataframe(df)
