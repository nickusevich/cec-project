from fastapi import FastAPI, HTTPException, Query
import redis
import json

app = FastAPI()

# Initialize Redis client
redis_client = redis.StrictRedis(host="redis-service", port=6379, db=0)



@app.get("/")
async def home():
    return {"Welcome to temperature observability API"}

@app.get("/temperature")
def get_experiment(
    experiment_id: str = Query(..., alias="experiment-id"),
    start_time: float = Query(..., alias="start-time"),
    end_time: float = Query(..., alias="end-time")
):
    # Retrieve the experiment data from Redis
    experiment_data = redis_client.hgetall(experiment_id)
    if not experiment_data:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    # Debug log
    # print(f"Retrieved data for {experiment_id}: {experiment_data}")

    # List to store parsed measurements
    parsed_measurements = []

    # Iterate over the experiment data
    for k, v in experiment_data.items():
        # Ignore non-measurement fields like thresholds, timestamps, and others
        key = k.decode('utf-8')
        if key in ['start_timestamp', 'terminated_timestamp', 'num_sensors', 'upper_threshold', 'lower_threshold', 'out_of_range', 'researcher', 'stabilization_timestamp', 'withinthreshold', 'notification_stab'] or key.startswith("out_of_range"):
            continue
        
        # Decode the value and load the JSON content

        timestamp = float(k)

        if start_time <= timestamp <= end_time:

            value_str = v.decode('utf-8')
            value_str = value_str.replace("'", '"')
            measurement_data = json.loads(value_str)


        # Append the measurement data (timestamps and temperatures) to the list
            parsed_measurements.append({
                "timestamp": measurement_data["timestamp"],
                "temperature": measurement_data["avg_temp"]
            })

    # Return the list of measurements as a response
    return parsed_measurements



@app.get('/temperature/out-of-range')
async def get_out_of_range(
    experiment_id: str = Query(..., alias="experiment-id")):

    experiment_data = redis_client.hgetall(experiment_id)

    if not experiment_data:
        raise HTTPException(status_code=404, detail="Experiment not found")

    # print(f"Retrieved data for {experiment_id}: {experiment_data}")

    parsed_measurements = []

    # Iterate over the experiment data
    for k, v in experiment_data.items():
        key = k.decode('utf-8')

        # Check if the key starts with "out_of_range"
        if key.startswith("out_of_range_"):
            value_str = v.decode('utf-8')
            value_str = value_str.replace("'", '"')

            measurement_data = json.loads(value_str)

            parsed_measurements.append({
                "timestamp": measurement_data["timestamp"],
                "temperature": measurement_data["avg_temp"]
            })

        # Continue to the next item
        continue

    return parsed_measurements


