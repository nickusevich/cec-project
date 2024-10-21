FROM python:3.8

WORKDIR /usr/src/app

RUN pip install confluent_kafka click fastavro redis requests avro

COPY ./*.py ./

VOLUME ["/usr/src/app/auth"]

ENTRYPOINT ["python3", "-u"]

