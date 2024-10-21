import redis
import json
from collections import defaultdict
import requests

class DataClient:
    event = ['ExperimentConfig', 'sensor_temperature_measured']
    def __init__(self):
        self.redis_client = redis.StrictRedis(host='127.0.0.1', port=6379, db=0)
        self.experiment_data = {} # Key: expermentid, val: list[timestamp: current_data / timestamp etc]
        self.notify_url = "localhost:3000/api/notify"

    def notify(self, req):
        """
        Calls the notifier API to notify about out-of-range or stabilized events.
        Arguments:
            req: A dictionary containing the notification data.
        Returns:
            response_text: The response text from the notification API.
        """
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'accept': '*/*'
        }

        try:
            # Send POST request to the notify API
            response = requests.post(
                self.notify_url,
                data=json.dumps(req),  # Convert the request data to JSON format
                headers=headers
            )

            # Check if the request was successful
            if response.status_code == 200:
                print(f"Notification sent successfully for measurement {req['measurement_id']}.")
            else:
                print(f"Failed to send notification: {response.status_code}, {response.text}")

            # Return the response text for further handling
            return response.text
        
        except Exception as e:
            print(f"Error sending notification: {str(e)}")
            return None  # Return None or some error message




    def flush_experiment(self, experiment_id):
        """
        Flushes the experiment's data from the application's memory into the database
        Arguments:
            experiment_id: String identifying experiment.
        """
        self.redis_client.hmset(experiment_id, {t: str(d) for t,d in self.experiment_data[experiment_id].items()})
        print(f'Notify for : {self.experiment_data[experiment_id]["out_of_range"]["measurement_id"]}')
       # self.notify({
       #     "notification_type": "OutOfRange",
       #     "researcher": self.experiment_data[experiment_id]["researcher"],
       #     "experiment_id": experiment_id,
       #     "measurement_id": self.experiment_data[experiment_id]["out_of_range"]["measurement_id"],
       #     "cipher_data": self.experiment_data[experiment_id]["out_of_range"]["cipher_data"]
       # })
        del self.experiment_data[experiment_id]



    def get_current_data(self, experiment_id, timestamp):
        """
        Returns the current data for an experiment's timestamp from self.experiment_data
        Arguments:
            experiment_id: String identifying experiment.
        """
        if timestamp not in self.experiment_data[experiment_id]:
            return None
        return self.experiment_data[experiment_id][timestamp]
    

    
    def set_experiment_attr(self, experiment_id, mapping):
        """
        Writes to self.experiment_data to the respective experiment's an attribute
        Arguments:
            experiment_id: String identifying experiment.
            mapping: Dict containing the key and the value
        """
        if experiment_id not in self.experiment_data:
            self.experiment_data[experiment_id] = {}
        self.experiment_data[experiment_id].update(mapping)



    def bounds_check(self, experiment_id, timestamp, measurement_id, cipher_data):
        """
        Compares measured average temperature against baseline. 
        Writes the current timestamp to 'out_of_range' key within the temperature's data
        Returns nothing
        Arguments:
            experiment_id: String identifying experiment.
            timestamp: timestamp of which to check the temperature
        """
        exp_data = self.experiment_data[experiment_id]
        oor_timestamp = float('inf')
        # oor_timestamp = float('inf')
        if "lower_threshold" not in exp_data:
            return
        if "out_of_range" in exp_data:
            oor_timestamp = exp_data["out_of_range"]["timestamp"]
        lower_threshold = exp_data["lower_threshold"]
        upper_threshold = exp_data["upper_threshold"]
        num_sensors = exp_data["num_sensors"]
        exp_started = "start_timestamp" in exp_data

        timestamp_data = exp_data[timestamp]

        num_measurements = timestamp_data["num_temps"]
        temp = timestamp_data["avg_temp"]
        if num_sensors != num_measurements:
            return
        else:
            print("Checking temperature")
           # print('Temperature Values : ', temp, lower_threshold, upper_threshold, timestamp, oor_timestamp, exp_started)

            if ((temp < lower_threshold or temp > upper_threshold) and exp_started):
                print('Reached All')

                self.set_experiment_attr(experiment_id, {f"out_of_range_{timestamp}": {"timestamp": timestamp, "measurement_id": measurement_id, "cipher_data": cipher_data, "AvgTemp": temp}})
            if (temp < lower_threshold or temp > upper_threshold) and timestamp < oor_timestamp and exp_started:
                print('Temperature Values : ', temp, lower_threshold, upper_threshold, timestamp, oor_timestamp, exp_started)

                #||||| The below line indicates the measurementID, timestamp, and cipher_data. SHOULD BE NOTIFIED BECAUSE IT IS OUT OF RANGE|||||
                self.set_experiment_attr(experiment_id, {"out_of_range": {"timestamp": timestamp, "measurement_id": measurement_id, "cipher_data": cipher_data}})
    

                self.notify({
                    "notification_type": "OutOfRange",
                    "researcher": "d.landau@uu.nl",
                    "experiment_id": experiment_id,
                    "measurement_id": measurement_id,
                    "cipher_data": cipher_data})
                    
    def process(self, message):
        """
        Processes messages>
        For a sensor_temperature_measured event
        Arguments:
            message: JSON containing the message to be parsed
        """
        experiment_id = message["experiment"]

        if message["name"] == "sensor_temperature_measured":
            print(message)
            measurement_id = message["measurement_id"]
            timestamp = message["timestamp"]
            current_temp = message["temperature"]
            current_data = self.get_current_data(experiment_id, timestamp)
            cipher_data = message["measurement_hash"]
            measurement_id = message["measurement_id"]
            if current_data != None:
                current_avg = current_data["avg_temp"]
                num_temps = current_data["num_temps"]
                avg_temp = ((num_temps*current_avg)+current_temp) / (num_temps +1)
                num_temps += 1
            else:
                avg_temp = current_temp
                num_temps = 1
            current_data = {
                "timestamp":timestamp,
                "measurement_id": measurement_id,
                "avg_temp": avg_temp,
                "num_temps": num_temps
            }
            self.set_experiment_attr(experiment_id, {timestamp: current_data})
            # Check temp here
            self.bounds_check(experiment_id, timestamp, measurement_id, cipher_data)

        elif message["name"] == "experiment_configured":
            print(message)
            upper_threshold = message["temperature_range"]["upper_threshold"]
            lower_threshold = message["temperature_range"]["lower_threshold"]
            researcher = message["researcher"]
            num_sensors = len(message["sensors"])
            self.set_experiment_attr(experiment_id, {"upper_threshold": upper_threshold})
            self.set_experiment_attr(experiment_id, {"lower_threshold": lower_threshold})
            self.set_experiment_attr(experiment_id, {"num_sensors": num_sensors})
            self.set_experiment_attr(experiment_id, {"researcher": researcher})

        
        elif message["name"] == "experiment_started":
            timestamp = message["timestamp"]
            # Bug workaround: Mutates the second 'experiment_started' msg to 'experiment_terminated' and flushes
            # When fixed, can remove code between here and comment below
            #if experiment_id in self.experiment_data:
            #    self.set_experiment_attr(experiment_id, {"terminated_timestamp": timestamp})
            #    self.flush_experiment(experiment_id)
            #else:
            # ^ ^ ^ ^ ^ ^ ^ 
            self.set_experiment_attr(experiment_id, {"start_timestamp": timestamp})

        elif message["name"] == "experiment_terminated":
            timestamp = message["timestamp"]
            self.set_experiment_attr(experiment_id, {"terminated_timestamp": timestamp})
            self.flush_experiment(experiment_id)


        elif message["name"] == "stabilization_started":
            timestamp = message["timestamp"]
            self.set_experiment_attr(experiment_id, {"stabilization_timestamp": timestamp})

        else:
            print("\t\t" + message["name"])

