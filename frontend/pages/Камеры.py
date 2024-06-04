import streamlit as st
import requests
import pandas as pd
from pages.utils.login import check_password

st.set_page_config(page_title="Добавить/Изменить/удалить информацию о камере", page_icon="📸")
st.title("Добавить/Удаление/редактирование информации о камере")

if not check_password():
    st.stop()

response = requests.get('http://backend:9032/camera/')
data = response.json()['cameras']
df = pd.DataFrame(data)
st.table(df)

action = st.selectbox('Выберете действие:', options=['Редактировать', 'Удалить', 'Добавить'])
dict_column = {"rtsp_stream": "rtsp stream",
               "name": "имя камеры",
               "description": "описание камеры",
               "camera_id": "id камеры"}

if action == 'Редактировать':
    if df.shape[0] == 0:
        st.write('Добавьте камеру')
    else:
        row_to_edit = st.number_input('Выберете номер поля камеры в таблице, которую хотите отредактировать',
                                      min_value=0,
                                      max_value=len(df) - 1, format="%d")
        none_field = False
        with st.form(key='edit_form'):
            new_data = {}
            for column in df.columns:
                change_field = st.text_input(f'Введите {dict_column.get(column)}')
                if change_field == "":
                    none_field = True
                new_data[column] = change_field
            submit_button = st.form_submit_button(label='ОТПРАВИТЬ')

        if submit_button:
            if none_field:
                st.write("Заполните все поля")
            else:
                response = requests.put(f'http://backend:9032/camera/{df.loc[row_to_edit, "camera_id"]}', json=new_data)
                if response.status_code == 200:
                    st.write('Запрос на изменение отправлен успешно')
                else:
                    st.write('Не удалось отправить запрос на изменение')
                    st.write(response.text)
elif action == 'Удалить':
    if df.shape[0] == 0:
        st.write('Добавьте камеру')
    else:
        row_to_edit = st.number_input('Выберете id камеры, которую хотите удалить', min_value=0,
                                      max_value=len(df) - 1, format="%d")
        if st.button('УДАЛИТЬ'):
            response = requests.delete(f'http://backend:9032/camera/{df.loc[row_to_edit, "camera_id"]}')
            if response.status_code == 200:
                st.write('Данные успешно удалены')
            else:
                st.write('Не удалось удалить данные')
                st.write(response.text)


elif action == 'Добавить':
    none_field = False
    submit_button = None
    if df.shape[0] >= 1:
        st.write('Нельзя добавить больше одной камеры. Вы можете удалить или отредактировать её.')
    else:
        with st.form(key='edit_form'):
            text_input = st.text_input("Введите название камеры")
            address = st.text_input("Введите rtsp-адрес камеры")
            description = st.text_input("Введите описание камеры")
            camera_id = st.number_input('Введите id камеры', min_value=0, format="%d")
            submit_button = st.form_submit_button(label='Отправить')

            if submit_button:
                if text_input == "" or address == "" or submit_button == "":
                    st.write("Заполните все поля")
                else:
                    response = requests.post('http://backend:9032/camera/',
                                             json={"name": text_input, "rtsp_stream": address,
                                                   "description": description, "camera_id": camera_id})
                    if response.status_code == 200:
                        st.write('Запрос на добавление отправлено успешно')
                    else:
                        st.write('Не удалось отправить запрос на добавление')
                        st.write(response.status_code)
                        st.write(response.text)
