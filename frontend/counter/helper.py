import cv2
import numpy as np
from fastapi import FastAPI
import streamlit as st
import time
import torch
from counter.yolo.model import YOLO
import datetime

app = FastAPI()

targets = []
color_purple = (255, 0, 255)
color_yellow = (0, 255, 255)
first_interval_arr = np.array([False, False, False])
second_interval_arr = np.array([False, False, False])
front_chiken = np.array([False, False, False])
image_size = (1920, 1080)


class Counter:
    def __init__(self, model, input_path, size_interval):
        self.input_path = input_path
        self.webcam = cv2.VideoCapture(input_path, cv2.CAP_FFMPEG)
        self.height = int(self.webcam.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(self.webcam.get(cv2.CAP_PROP_FRAME_WIDTH))

        self.full_area = self.height * self.width
        self.model = model
        self.size_interval = size_interval
        self.right_interval = False
        self.check_double_chic_first = False

        if self.height > self.width:
            self.middle, self.divide_to_three = int(self.height / 2), int(self.height / 3)
            self.line_point1_left, self.line_point2_left = (0, self.middle - 100), (self.width, self.middle - 100)
            self.line_point1_middle, self.line_point2_middle = (0, self.middle + 100), (self.width, self.middle + 100)
            self.interval_middle = (self.width - 100, self.width + 100)
        else:
            self.middle, self.divide_to_three = int(self.width / 2), int(self.width / 3)

            self.interval_first = np.array([self.middle - 3 * self.size_interval, self.middle - self.size_interval])
            self.interval_second = np.array([self.middle - self.size_interval, self.middle + self.size_interval])
            self.interval_third = np.array([self.middle + self.size_interval, self.middle + 4 * self.size_interval])

            self.line_point1_left_left, self.line_point2_left_left = (self.interval_first[0], 0), (
                self.interval_first[0], self.height)

            self.line_point1_left, self.line_point2_left = (self.interval_first[1], 0), (
                self.interval_first[1], self.height)

            self.line_point1_middle, self.line_point2_middle = (self.interval_second[1], 0), (
                self.interval_second[1], self.height)

            self.line_point1_right, self.line_point2_right = (self.interval_third[1], 0), (
                self.interval_third[1], self.height)

        self.fps = 29
        self.fpm = self.fps * 60
        self.line_back = np.array([False, False, False])

    def draw_lines(self, frame):
        """Draw line on frame"""
        cv2.line(frame, self.line_point1_left_left, self.line_point2_left_left, (255, 0, 0), 10)
        cv2.line(frame, self.line_point1_left, self.line_point2_left, (255, 0, 0), 10)
        cv2.line(frame, self.line_point1_middle, self.line_point2_middle, (255, 0, 0), 10)
        cv2.line(frame, self.line_point1_right, self.line_point2_right, (255, 0, 0), 10)

        cv2.line(frame, (0, self.divide_to_three + 130), (
            self.width, self.divide_to_three + 130), (0, 0, 255), 10)

        cv2.line(frame, (0, self.divide_to_three - 300), (
            self.width, self.divide_to_three - 300), (0, 0, 255), 10)

    def draw_centers(self, frame, x, y, area):
        """Draw rectangle of chicken"""
        cv2.circle(frame, (x, y), 5, (255, 0, 0), -1)
        cv2.putText(frame,
                    f"Chicken area = {area}",
                    (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255)
                    )

    def speed(self, frame, speed_second, speed_minute, count, frame_count):
        frame = cv2.putText(frame,
                            f'frame_count = {frame_count}',
                            (self.width - 400, 160),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            color_purple,
                            4
                            )
        frame = cv2.putText(frame,
                            f'count = {count}',
                            (self.width - 400, 130),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            color_purple,
                            4
                            )

        frame = cv2.putText(frame,
                            f'speed per second = {speed_second}',
                            (self.width - 400, 100),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            color_purple,
                            4
                            )

        frame = cv2.putText(frame,
                            f'speed per minute = {speed_minute}',
                            (self.width - 400, 70),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            color_purple,
                            4
                            )
        return frame

    def check_lines(self, center_y):
        """Check line of chicken"""
        if self.divide_to_three + 130 <= center_y <= self.height:
            return 0
        elif self.divide_to_three - 300 <= center_y < self.divide_to_three + 130:
            return 1
        elif 0 <= center_y < self.divide_to_three - 300:
            return 2

    def check_chicken_behind(self, front_chic_center, index_interval, boxes, area):
        """Сheck if there is a chicken in behind"""
        for box in boxes:
            if box.conf[0] > 0.4 and self.full_area / area > 8:
                behind_chic_center, y, _, _ = box.xywh[0]
                line = self.check_lines(y)
                if (0 < front_chic_center - behind_chic_center < 700) and line == index_interval:
                    return True
        return False

    def check_chicken_front(self, front_chic_center, index_interval, boxes, area):
        """Сheck if there is a chicken in front"""
        for box in boxes:
            if box.conf[0] > 0.4 and self.full_area / area > 8:
                behind_chic_center, y, _, _ = box.xywh[0]
                line = self.check_lines(y)
                if (700 < front_chic_center - behind_chic_center < 0) and line == index_interval:
                    return True
        return False

    def draw_contours_and_count(self, frame, frame_count):
        """Draw contours of object on video"""
        count_chicken = 0
        results = self.model.predict(frame, save=False, verbose=False)
        for result in results:
            boxes = result.boxes
            for box in boxes:
                confidence = box.conf[0]
                cx, cy, w, h = box.xywh[0]
                cx, cy, w, h = int(cx), int(cy), int(w), int(h)
                area = w * h
                if confidence > 0.4 and self.full_area / area > 8:
                    frame = cv2.rectangle(frame,
                                          (cx - int(w / 2), cy - int(h / 2)),
                                          (cx - int(w / 2) + w, cy - int(h / 2) + h),
                                          (0, 255, 255),
                                          2
                                          )
                    center1, center2 = (cy, cx) if self.height > self.width else (cx, cy)
                    self.draw_centers(frame, center1, center2, area)
                    index_interval = self.check_lines(center2)
                    front_chiken[index_interval] = self.check_chicken_front(center1, index_interval, boxes, area)

                    if self.interval_second[0] < center1 and frame_count == 0:
                        count_chicken += 1
                        continue

                    elif self.interval_first[0] < center1 <= self.interval_first[1]:
                        if front_chiken[index_interval]:
                            self.check_double_chic_first = True

                        if front_chiken[index_interval] and (
                                second_interval_arr[index_interval] or first_interval_arr[index_interval]):
                            first_interval_arr[index_interval] = False
                            second_interval_arr[index_interval] = False

                        if not first_interval_arr[index_interval]:
                            if self.full_area / area < 10:
                                count_chicken += 2
                            else:
                                count_chicken += 1
                            first_interval_arr[index_interval] = True

                        front_chiken[index_interval] = False

                    elif self.interval_second[0] < center1 <= self.interval_second[1]:
                        if front_chiken[index_interval] and (
                                second_interval_arr[index_interval] or first_interval_arr[index_interval]):
                            first_interval_arr[index_interval] = False
                            second_interval_arr[index_interval] = False

                        if not first_interval_arr[index_interval]:
                            if not second_interval_arr[index_interval]:

                                if self.full_area / area < 10:
                                    count_chicken += 2
                                else:
                                    count_chicken += 1
                                second_interval_arr[index_interval] = True
                    else:
                        if self.interval_third[0] <= center1 <= self.interval_third[1]:
                            behind_chicken = self.check_chicken_behind(center1, index_interval, boxes, area)

                            if behind_chicken and self.check_double_chic_first:
                                first_interval_arr[index_interval] = True
                                second_interval_arr[index_interval] = False
                                self.check_double_chic_first = False
                            else:
                                first_interval_arr[index_interval] = False
                                second_interval_arr[index_interval] = False
                                self.check_double_chic_first = False

        return frame, count_chicken

    def display_video(self):
        count_chicken_sec = 0
        count_chicken_min = 0
        frame_count = 0
        speed_second = 0
        speed_minute = 0
        all_count = st.session_state.all_count
        st_frame_image = st.empty()
        st_frame_text = st.empty()
        st_empty_bitrate = st.empty()
        while st.session_state.video_running:
            if not self.webcam.isOpened():
                self.webcam.release()
                time.sleep(10)
                if not self.webcam.isOpened():
                    self.webcam.release()
                    st.error("Камера недоступна")
                    break

            ret, imageFrame = self.webcam.read()
            st_empty_bitrate.write(f'битрейт = {self.webcam.get(cv2.CAP_PROP_BITRATE)}')
            if not ret:
                self.webcam.release()
                time.sleep(10)
                ret, imageFrame = self.webcam.read()
                if not ret:
                    st.write("Камера доступна, но не получает кадры по какой-то причине. Попробуем ее пересоздать")
                    self.webcam.release()

                    start = datetime.datetime.now()
                    self.webcam = cv2.VideoCapture(self.input_path)
                    finish = datetime.datetime.now()

                    st_empty_bitrate('Время работы: ' + str(finish - start))
                    ret, imageFrame = self.webcam.read()
                    if not ret:
                        st.error("Камера доступна, но не получает кадры по какой-то причине. Не получилось")
                        # битрейт видеопотока
                        st.write("Video Bitrate: {} kbps".format(self.webcam.get(cv2.CAP_PROP_BITRATE)))
                        # кодек видеопотока
                        st.write("Video Codec: {}".format(self.webcam.get(cv2.CAP_PROP_FOURCC)))
                        self.webcam.release()
                        break

            imageFrame, count = self.draw_contours_and_count(imageFrame, frame_count)
            all_count += count
            st.session_state.all_count = all_count
            count_chicken_sec += count
            count_chicken_min += count

            if frame_count % int(self.fps) == 0:
                speed_second = count_chicken_sec
                count_chicken_min += count_chicken_sec
                count_chicken_sec = 0

            if frame_count % int(self.fpm) == 0:
                count_chicken_min = all_count
                speed_minute += count_chicken_min
                count_chicken_min = 0

            imageFrame = self.speed(imageFrame, speed_second, speed_minute, all_count, frame_count)
            frame_count += 1
            st_frame_text.text(
                f'КОЛИЧЕСТВО ЦЫПЛЯТ В МИНУТУ: {speed_minute}\nКОЛИЧЕСТВО ЦЫПЛЯТ В СЕКУНДУ: {speed_second}\nОБЩЕЕ КОЛИЧЕСТВО ЦЫПЛЯТ: {all_count} ')

            if frame_count % 2 == 0:
                st_frame_image.image(imageFrame,
                                     caption='Detected Video',
                                     channels="BGR",
                                     use_column_width=True, width=50)
        self.webcam.release()


def run_counting(model_path, input_path):
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        model = YOLO(model_path)
        model.to(device)

        counter = Counter(model, input_path, 120)
        counter.display_video()

    except Exception as ex:
        st.error(f"Не удалось загрузить модель детекции или недоступно ни CPU, ни GPU. Проверьте путь: {model_path}")
        st.error(ex)
