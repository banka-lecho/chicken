import streamlit as st
import requests
import base64
from pages.utils.login import check_password
import pandas as pd

st.set_page_config(page_title="Изменить информации", page_icon="📥")
st.title("Изменение информации о партии")
st.sidebar.header("Изменение информации")

if not check_password():
    st.stop()

response = requests.get('http://backend:9032/chickens/')
data = response.json()['chickens']
df = pd.DataFrame(data)
st.dataframe(df)
with st.form(key="change_field"):
    batch_id = st.text_input("Введите номер партии")
    fields_dict = {
        "Номер линии": "line_number",
        "Номер машины": "machine_id",
        "Количество цыплят": "count",
        "Кросс": "cross_"}
    field_key = st.selectbox("Введите название поля, которое хотите изменить", fields_dict.keys())
    field = fields_dict.get(field_key)
    new_value = st.text_input("Введите новое значение поля")
    submit_button = st.form_submit_button(label='Отправить')

if submit_button:
    if batch_id == "" or field == "" or new_value == "":
        st.write("Заполните все поля")
    else:
        if batch_id in df['batch_id'].values:
            response = requests.put(f'http://backend:9032/chickens/{str(batch_id)}/{str(field)}/{str(new_value)}',
                                    json={"batch_id": batch_id, "field": field, "new_value": new_value})
            if response.status_code == 200:
                st.markdown("<span style='color:green'>Запрос на изменение отправлен успешно</span>",
                                    unsafe_allow_html=True)
            else:
            	st.markdown("<span style='color:red'>Не удалось отправитиь запрос на изменение</span>",
                                    unsafe_allow_html=True)
        else:
            st.write('Данного номера партии нет в таблице базы данных')
            st.markdown("<span style='color:red'>Данного номера партии нет в таблице базы данных</span>",
                                    unsafe_allow_html=True)

