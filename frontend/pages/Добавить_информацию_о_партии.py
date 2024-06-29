import time
from pathlib import Path
import requests
import pandas as pd
import streamlit as st
import os
import cv2
import counter.helper as helper
import pages.utils.settings as settings
from streamlit_drawable_canvas import st_canvas
from PIL import Image
from pages.utils.login import check_password
import datetime

# заголовки
st.set_page_config(
    page_title="Object Detection using YOLOv8",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Подсчёт объектов")
st.sidebar.header("Детекция и подсчёт объектов")

# аутентификация
if not check_password():
    st.stop()


def clicked(button):
    """
    Функция для изменения состояния сессионой переменной, которая отвечает за переключение трех кнопок
    - кнопка "Подключиться к камере"
    - кнопка "Пуск"
    - кнопка "Отправить данные"
    """
    st.session_state.clicked[button] = True


# инициализация сессионных переменных
if 'end_of_stream' not in st.session_state:
    st.session_state.end_of_stream = 0
if 'all_count' not in st.session_state:
    st.session_state.all_count = 0
if 'clicked' not in st.session_state:
    st.session_state.clicked = {1: False, 2: False, 3: False}
if 'video_running' not in st.session_state:
    st.session_state.video_running = False


def send_message_clean_cache(message: str, clean_cache=False, color="red"):
    """Функция для отображения ошибки/успеха операции и освобождения сессионых переменных"""
    st.markdown(
        f"<span style='color:{color}'>{message}</span>", unsafe_allow_html=True)
    if clean_cache:
        for key in st.session_state.keys():
            del st.session_state[key]
        st.stop()


def toggle_video():
    """Функция для запуска/остановки видеопотока"""
    st.session_state.video_running = not st.session_state.video_running


response = requests.get('http://backend:9032/camera/')
data = response.json()['cameras']
df = pd.DataFrame(data)
response_chickens = requests.get('http://backend:9032/chickens/')
data_chickens = response_chickens.json()['chickens']
df_chickens = pd.DataFrame(data_chickens)
count_chickens = 0
if df.shape[0] == 0:
    st.write(
        'Чтобы внести информацию о партии, нужно добавить камеру. Вы можете это сделать  на странице "✍️ Добавить камеру"')
else:
    # ввод данных
    batch_id = st.sidebar.text_input("Введите номер партии")
    line_number = st.sidebar.number_input("Введите номер линии", min_value=0, step=1, format="%d")
    cross_ = st.sidebar.text_input("Введите номер кросс")
    number_machine = st.sidebar.number_input("Введите номер машины", min_value=0, step=1, format="%d")
    if "check_duplicate" not in st.session_state:
        st.session_state.check_duplicate = True
        if not df_chickens.empty and batch_id in df_chickens['batch_id'].values:
            send_message_clean_cache(
                "Поле с данным номером партии уже существует. Добавьте другой номер или отредактируйте поле.",
                clean_cache=True,
                color="red")

    # проверка камеры
    response_camera = requests.get('http://backend:9032/camera')
    if response_camera.status_code == 200:
        sources = response_camera.json()
        sources = [(camera['name'], camera['rtsp_stream']) for camera in sources['cameras']]
        stream_address = str(sources[0][1])
        st.sidebar.write(f'КАМЕРА: {str(sources[0][0])}')
        submit_button = st.sidebar.button('ПОДКЛЮЧИТЬСЯ К КАМЕРЕ', on_click=clicked, args=[1])
        st_empty = st.empty()
        submit_button_count = None
        model_path = Path(settings.DETECTION_MODEL)
        if st.session_state.clicked[1]:
            if "response_count" not in st.session_state:
                # проверка на пустоту
                if batch_id == "" or line_number == "" or cross_ == "" or number_machine == "":
                    send_message_clean_cache("Заполните все поля",
                                             clean_cache=True,
                                             color="red")

                # отправление первичных данных
                st.session_state.response_count = True
                response_count = requests.post('http://backend:9032/chickens/',
                                               json={"batch_id": batch_id,
                                                     "start_time": datetime.datetime.now().strftime(
                                                         "%Y-%m-%d %H:%M:%S"),
                                                     "end_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                                     "line_number": line_number,
                                                     "machine_id": number_machine,
                                                     "count": count_chickens,
                                                     "cross_": cross_})

                if response_count.status_code != 200:
                    send_message_clean_cache(
                        "Не удалось отправить запрос на первичное добавление. Возможно произошла дупликация номера партии",
                        clean_cache=True,
                        color="red")
            else:
                # проверка жизнедеятельности камеры
                cap = cv2.VideoCapture(stream_address)
                while not cap.isOpened():
                    st_empty.markdown("<span style='color:red'>ИДЁТ ПОДКЛЮЧЕНИЕ...</span>", unsafe_allow_html=True)
                time.sleep(2)
                cap.release()
                st_empty.markdown("<span style='color:green'>ПОДКЛЮЧЕНИЕ ЕСТЬ</span>", unsafe_allow_html=True)

            st.sidebar.header("Управление запуском")
            if 'start' not in st.session_state:
                st.session_state.start = datetime.datetime.now()

            # Создание кнопки для запуска/остановки видеопотока (при каждой остановке видеопотока в бд отправляются данные)
            if st.sidebar.button('ПУСК'):
                toggle_video()
                helper.run_counting(model_path, stream_address)
                count = st.session_state.all_count
                response_count = requests.put(f'http://backend:9032/chickens/{str(batch_id)}/count/{str(count)}',
                                              json={"batch_id": batch_id,
                                                    "field": "count",
                                                    "new_value": count})
                if response_count.status_code != 200:
                    send_message_clean_cache("Не удалось отправить запрос на изменение",
                                             clean_cache=True,
                                             color="red")
            # создание кнопки "Отправить данные".
            button_send = st.sidebar.button('Отправить данные', on_click=clicked, args=[3],
                                            disabled=st.session_state.clicked[3])
            if st.session_state.clicked[3]:
                st.session_state.all_count = 0
                start = st.session_state.start.strftime("%Y-%m-%d %H:%M:%S")
                finish = datetime.datetime.now()
                finish = finish.strftime("%Y-%m-%d %H:%M:%S")
                # поскольку в бд уже существует поле с нужным id, то я просто отправляю правильное время в бд
                response = requests.put(f'http://backend:9032/chickens/{batch_id}/{start}/{finish}',
                                        json={batch_id: batch_id, "start_time": start, "end_time": finish})
                if response.status_code == 200:
                    send_message_clean_cache("Запрос на добавление отправлен успешно.",
                                             clean_cache=True,
                                             color="green")
                else:
                    send_message_clean_cache("Не удалось отправить запрос на вторичное добавление.",
                                             clean_cache=True,
                                             color="red")
    else:
        st.write('Не удалось получить доступ к камере!')
