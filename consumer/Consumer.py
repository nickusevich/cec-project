import json
import avro.schema
import signal
import click
import random
import os
from fastavro import reader
from Dataclient import DataClient
from io import BytesIO
from confluent_kafka import Consumer
from avro.datafile import DataFileReader, DataFileWriter
from avro.io import DatumReader, DatumWriter, BinaryDecoder

dataClient = DataClient()

def signal_handler(sig, frame):
    print('EXITING SAFELY!')
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)

c = Consumer({
    'bootstrap.servers': '13.60.146.188:19093,13.60.146.188:29093,13.60.146.188:39093',
    'group.id': f"{random.random()}",
    'auto.offset.reset': 'latest',
    'enable.auto.commit': 'true',
    'security.protocol': 'SSL',
    'ssl.ca.location': './auth/ca.crt',
    'ssl.keystore.location': './auth/kafka.keystore.pkcs12',
    'ssl.keystore.password': 'cc2023',
    'ssl.endpoint.identification.algorithm': 'none',
})

@click.command()
@click.argument('topic')
def consume(topic: str):
    c.subscribe(
        [topic],
        on_assign=lambda _, p_list: print(p_list)
    )

    num_events = 0
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        num_events += 1
        if num_events % 1000 == 0:
            print(num_events)

        byte_stream = BytesIO(msg.value())
       # avro_schema = reader(byte_stream)
        name = msg.headers()[0][1].decode("utf-8")
       # print(f'The event name {num_events} is ->',name)
       # for record in avro_schema:
       #     record["name"] = name
       #     dataClient.process(record)

        while byte_stream.tell() < len(msg.value()):
            #avro_schema = reader(message_bytes)
            reader = DataFileReader(byte_stream, DatumReader())
           # name = msg.headers()[0][1].decode("utf-8")
            print('The event name is ->',name)
           # print('This is the reader variable : ',reader)
            for record in reader:
                record["name"] = name
                dataClient.process(record)



consume()
