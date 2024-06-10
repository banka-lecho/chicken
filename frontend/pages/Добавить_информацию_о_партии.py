import time
from pathlib import Path
import requests
import pandas as pd
import cv2
import streamlit as st
import os
import pages.utils.helper as helper
import pages.utils.settings as settings
from pages.yolo.model import YOLO
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pages.utils.login import check_password
import datetime

st.set_page_config(
    page_title="Object Detection using YOLOv8",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Подсчёт объектов")
st.sidebar.header("Детекция и подсчёт объектов")


if not check_password():
    st.stop()

if 'end_of_stream' not in st.session_state:
    st.session_state.end_of_stream = 0

if 'all_count' not in st.session_state:
    st.session_state.all_count = 0

# Initialize the key in session state
if 'clicked' not in st.session_state:
    st.session_state.clicked = {1:False,2:False,3:False}

# Function to update the value in session state
def clicked(button, value_count):
    st.session_state.clicked[button] = True
    st.session_state.all_count = value_count

response = requests.get('http://backend:9032/camera/')
data = response.json()['cameras']
df = pd.DataFrame(data)
response_chickens = requests.get('http://backend:9032/chickens/')
data_chickens = response_chickens.json()['chickens']
df_chickens = pd.DataFrame(data_chickens)
all_count = 0
count_chickens=0
if df.shape[0] == 0:
    st.write(
        'Чтобы внести информацию о партии, нужно добавить камеру. Вы можете это сделать  на странице "✍️ Добавить камеру"')
else:
    model_path = Path(settings.DETECTION_MODEL)
    try:
        model = YOLO(model_path)
    except Exception as ex:
        st.error(f"Не удалось загрузить модель детекции. Проверьте путь: {model_path}")
        st.error(ex)
    batch_id = st.sidebar.text_input("Введите номер партии")
    line_number = st.sidebar.number_input("Введите номер линии", min_value=0, step=1, format="%d")
    cross_ = st.sidebar.text_input("Введите номер кросс")
    number_machine = st.sidebar.number_input("Введите номер машины", min_value=0, step=1, format="%d")

    response_camera = requests.get('http://backend:9032/camera')
    if response_camera.status_code == 200:
        sources = response_camera.json()
        sources = [(camera['name'], camera['rtsp_stream']) for camera in sources['cameras']]
        # stream_address = str(sources[0][1])
        stream_address = str(settings.VIDEO_PATH)
        st.sidebar.write(f'КАМЕРА: {str(sources[0][0])}')
        submit_button = st.sidebar.button('ПОДКЛЮЧИТЬСЯ К КАМЕРЕ', on_click=clicked, args=[1, count_chickens])
        st_empty = st.empty()
        submit_button_count = None

        if st.session_state.clicked[1]:
            if batch_id == "" or line_number == "" or cross_ == "" or number_machine == "":
                st.markdown(
                    "<span style='color:red'>Заполните все поля</span>", unsafe_allow_html=True)
                for key in st.session_state.keys():
                        del st.session_state[key]

            elif not df_chickens.empty and batch_id in df_chickens['batch_id'].values:
                st.markdown(
                    "<span style='color:red'>Поле с данным номером партии уже существует. Добавьте другой номер или отредактируйте поле.</span>",
                    unsafe_allow_html=True)
                for key in st.session_state.keys():
                        del st.session_state[key]

            else:
                st_empty.markdown("<span style='color:red'>ИДЁТ ПОДКЛЮЧЕНИЕ...</span>", unsafe_allow_html=True)
                time.sleep(2)
                st_empty.markdown("<span style='color:green'>ПОДКЛЮЧЕНИЕ ЕСТЬ</span>", unsafe_allow_html=True)
                st.sidebar.header("Управление запуском")
                if 'start' not in st.session_state:
                        st.session_state.start = datetime.datetime.now()

                if st.sidebar.toggle('ПУСК', on_change=clicked, args=[2, count_chickens]) and st.session_state.end_of_stream == 0:
                        count_chickens, end_of_stream = helper.run_counting(model, stream_address)
                        st.session_state.all_count = count_chickens
                        st.session_state.end_of_stream = end_of_stream
                        st.session_state.clicked[2] = False

                button_send = st.sidebar.button('Отправить данные', on_click=clicked, args=[3, count_chickens])
                if st.session_state.clicked[3]:
                                st.session_state.clicked[2] = False
                                st.session_state.end_of_stream = 1


                if not st.session_state.clicked[2] and st.session_state.end_of_stream == 1 and st.session_state.clicked[3]:
                        start = st.session_state.start.strftime("%Y-%m-%d %H:%M:%S")
                        finish = datetime.datetime.now()
                        finish = finish.strftime("%Y-%m-%d %H:%M:%S")
                        response = requests.post('http://backend:9032/chickens/',
                                         json={"batch_id": batch_id, "start_time": start,
                                               "end_time": finish, "line_number": line_number,
                                               "machine_id": number_machine,
                                               "count": st.session_state.all_count, "cross_": cross_})
                        if response.status_code == 200:
                                st.markdown("<span style='color:green'>Запрос на добавление отправлен успешно</span>",
                                        unsafe_allow_html=True)
                                for key in st.session_state.keys():
                                        del st.session_state[key]
                        else:
                                st.markdown("<span style='color:red'>Не удалось отправить запрос на добавление</span>",
                                        unsafe_allow_html=True)
                                st.write(response.status_code)
                                st.write(response.text)
                                for key in st.session_state.keys():
                                        del st.session_state[key]
    else:
        st.write('Failed to get sources')
