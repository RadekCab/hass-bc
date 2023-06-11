import asyncio
import uuid
import utils
import mqtt
from asyncio_paho import AsyncioPahoClient
from sensors import LocationSensor
from sensors import Sensor
from agent.agents import ReflexAgent
from user import User


async def connect_to_topic(sensors : list):
    
    response = ""
    for sensor in sensors:  
        async with AsyncioPahoClient(str(sensor.uuid)) as client:
            topic = sensor.get_topic()
            print(topic)
            client.username_pw_set(username="hass",password="nimda")
            #client.user_data_set(utils.get_json_payload(sensor))
            response = await mqtt.listen_to_topic(client, topic)
            await asyncio.sleep(5)
            #await mqtt.listen_to_topic(client, topic, response)
            #client.user_data_set(19)
            #await asyncio.sleep(5)
            print("RESPONSE INSIDE MAIN LOOP", client._userdata)

    print("RESPONSE OUTSIDE MAIN LOOP", response)
    
    
        
def setup():
    sensors = []
    #room1_location_sensor = LocationSensor("house/room1/temperature")
    #room1_location_sensor = LocationSensor("outside/temperature")
    #agent = ReflexAgent("room1/user/temp_decrease")
    agent = ReflexAgent("house/room1/temperature")
    #user = User("house/room1/users/add")
    #sensors.append(room1_location_sensor)
    sensors.append(agent)
    #sensors.append(room2_location_sensor)
    asyncio.run(connect_to_topic(sensors))
    

async def await_start_simulation():
    pass
  
        
        
if __name__ == "__main__":
    #asyncio.run(await_start_simulation())
    # add sensors
    setup()
    # make them publish on topics
    print("Disconnected.")
        
    
    