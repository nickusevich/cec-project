FROM python:3.8

WORKDIR /usr/src/app

RUN pip install fastapi fastavro redis requests click confluent_kafka uvicorn

COPY app.py ./

VOLUME ["/usr/src/app/auth"]

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]


