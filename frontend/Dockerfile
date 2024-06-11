FROM python:3.11

COPY requirements.txt app/requirements.txt
WORKDIR /app

RUN pip install -r requirements.txt
RUN pip install supervision
RUN pip install streamlit_drawable_canvas
COPY . /app

EXPOSE 9031

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=9031", "--server.address=0.0.0.0"]
