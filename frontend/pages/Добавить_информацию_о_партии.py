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

st.set_page_config(
    page_title="Object Detection using YOLOv8",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("Подсчёт объектов")

st.sidebar.header("Детекция и подсчёт объектов")

from pages.utils.login import check_password

if not check_password():
    st.stop()

response = requests.get('http://backend:9032/camera/')
data = response.json()['cameras']

df = pd.DataFrame(data)

response_chickens = requests.get('http://backend:9032/chickens/')
data_chickens = response_chickens.json()['chickens']
df_chickens = pd.DataFrame(data_chickens)

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
        stream_address = str(sources[0][1])
        # stream_address = str(settings.VIDEO_PATH)
        st.sidebar.write(f'КАМЕРА: {str(sources[0][0])}')
        submit_button = st.sidebar.button('ПОДКЛЮЧИТЬСЯ К КАМЕРЕ')
        st_empty = st.empty()
        submit_button_count = None

        if submit_button:
            if not df_chickens.empty:
                if batch_id in df_chickens['batch_id'].values:
                    st.markdown(
                        "<span style='color:red'>Поле с данным номером партии уже существует. Добавьте другой номер или отредактируйте поле.</span>",
                        unsafe_allow_html=True)
            else:
                st_empty.markdown("<span style='color:red'>ИДЁТ ПОДКЛЮЧЕНИЕ...</span>", unsafe_allow_html=True)
                time.sleep(2)
                st_empty.markdown("<span style='color:green'>ПОДКЛЮЧЕНИЕ ЕСТЬ</span>", unsafe_allow_html=True)
                time.sleep(3)
                count_chickens, start, finish = helper.run_counting(model, stream_address)
                start = start.strftime("%Y-%m-%d %H:%M:%S")
                finish = finish.strftime("%Y-%m-%d %H:%M:%S")
                response = requests.post('http://backend:9032/chickens/',
                                         json={"batch_id": batch_id, "start_time": start,
                                               "end_time": finish, "line_number": line_number,
                                               "machine_id": number_machine,
                                               "count": count_chickens, "cross_": cross_})
                if response.status_code == 200:
                    st.markdown("<span style='color:green'>Запрос на добавление отправлен успешно</span>",
                                unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:red'>Не удалось отправить запрос на добавление</span>",
                                unsafe_allow_html=True)
                    st.write(response.status_code)
                    st.write(response.text)

    else:
        st.write('Failed to get sources')
