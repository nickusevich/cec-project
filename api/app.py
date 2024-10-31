import aioredis
from fastapi import FastAPI, HTTPException, Query
import json

app = FastAPI()

# Initialize the Redis client
redis_client = None

@app.on_event("startup")
async def startup_event():
    global redis_client
    # Using default connection pool settings
    redis_pool = aioredis.ConnectionPool.from_url(
        "redis://redis-service:6379")
    redis_client = aioredis.Redis(connection_pool=redis_pool)

@app.on_event("shutdown")
async def shutdown_event():
    if redis_client:
        await redis_client.close()

@app.get("/")
async def home():
    return {"Welcome to TEMPERATURE OBSERVABILITY API"}

@app.get("/temperature")
async def get_experiment(
    experiment_id: str = Query(..., alias="experiment-id"),
    start_time: float = Query(..., alias="start-time"),
    end_time: float = Query(..., alias="end-time")
):
    # Retrieve the experiment data from Redis
    experiment_data = await redis_client.hgetall(experiment_id)
    if not experiment_data:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    parsed_measurements = []

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
    experiment_id: str = Query(..., alias="experiment-id")
):
    experiment_data = await redis_client.hgetall(experiment_id)
    
    if not experiment_data:
        raise HTTPException(status_code=404, detail="Experiment not found")
    
    parsed_measurements = []
    
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

