import streamlit as st
from st_pages import Page, show_pages
from pages.utils.login import check_password

st.markdown("# Главная страница")


def render_sidebar():
    """Render the sidebar only if the password is correct."""
    if st.session_state.get("password_correct", False):
        pass


def render_main_content():
    """Render the main content only if the password is correct."""
    if st.session_state.get("password_correct", False):
        show_pages(
            [
                Page("app.py", "Главная страница"),
                Page("pages/Камеры.py", "Камеры"),
                Page("pages/Внести_изменения_о_партии.py", "Внести изменения о партии"),
                Page("pages/Добавить_информацию_о_партии.py", "Добавить информацию о партии"),
                Page("pages/Посмотреть_статистику.py", "Посмотреть статистику")
            ]
        )
        st.write('ПРАВИЛА ПОЛЬЗОВАНИЯ:')
        st.write(
            '1) Чтобы внести информацию о партии цыплят, нужно заполнить все следующие поля на странице "Добавить информацию о партии": \n'
            '- номер партии \n'
            '- номер линии \n'
            '- номер кросс \n'
            '- номер машины')

        st.write(
            '2) Чтобы внести информацию о камере (удалить, редактировать, добавить), нужно заполнить все следующие поля на странице "Камеры": \n'
            '- название камеры \n'
            '- rtsp-адрес \n'
            '- описание камеры')


if not check_password():
    st.stop()

render_sidebar()
render_main_content()
