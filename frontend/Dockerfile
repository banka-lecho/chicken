FROM python:3.11

COPY requirements.txt app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install streamlit_drawable_canvas
RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y
COPY . /app

EXPOSE 9031

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=9031", "--server.address=0.0.0.0"]
