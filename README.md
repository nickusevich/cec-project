1) create consumer container, and run producer to receive temperature measure and have them saved in redis at localhost
COMMANDS: 

docker build -t consumer . 

docker run --network="host" --name consumer -v "$(pwd)/auth":/usr/src/app/auth consumer Consumer.py "group6"

2) after you launched consumer and producer properly, go to "api" folder and type the following commands:
COMMANDS:

docker build -t api .

docker run --network="host" api


3) after the app is working, we can extract experiments with specific start_time, end_time and experiment_id (send the request from your local machine, UBUNTU)
COMMAND:

curl -X GET http://localhost:8000/temperature -G \
    -d "{{EXPERIMENT_ID}}" \
    -d "start_time={{START_TIME}}" \
    -d "end_time={{END_TIME}}"
