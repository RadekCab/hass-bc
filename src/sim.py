import asyncio
import uuid
import utils
import mqtt
from asyncio_paho import AsyncioPahoClient
import time

from sensors import LocationSensor
from sensors import Sensor
from agent.agents import ReflexAgent
from user import User


async def connect_to_topic(sensor):
    response = ""
    #for sensor in sensors:  
    async with AsyncioPahoClient(str(sensor.uuid)) as client:
        print(sensor.get_topic())
        client.username_pw_set(username="hass",password="nimda")
        #client.user_data_set(utils.get_json_payload(sensor))
        response = await mqtt.listen_to_topic(client, sensor.get_topic())
        # TODO maybe task would be better here
        await asyncio.sleep(3)
        #await mqtt.listen_to_topic(client, topic, response)
        #client.user_data_set(19)
        #await asyncio.sleep(5)
        print(F"RESPONSE INSIDE MAIN LOOP {client._userdata} RECEIVED BY {client._client_id}")
        response = client._userdata

    return response
    
    
"""
return 2d array, first axis = heating requests, second axis = stop heating requests 
"""
async def get_requests_by_time(seconds : int, topic : str, sensors : list):
    ret_arr = []
    t_end = time.time() + seconds
    while time.time() < t_end:
        payload = await connect_to_topic(sensors)
        await asyncio.sleep(2)
        if str(payload) != "nothing":
            ret_arr.append(payload)
    return ret_arr
        
        
async def setup_noheat_listen():
    #sensors1 = []
    lock = asyncio.Lock()
    agent1 = ReflexAgent("room1/plan/noheating")
    #sensors1.append(agent1)
    return await get_requests_by_time(14, agent1.get_topic, agent1)
    
async def setup_heating_listen():
    await asyncio.sleep(2)
    #sensors2 = []
    lock = asyncio.Lock()
    agent2 = ReflexAgent("room1/plan/heating")
    #sensors2.append(agent2)
    return await get_requests_by_time(28, agent2.get_topic, agent2)

async def gather_heat_requests():
    group = await asyncio.gather(setup_heating_listen(), setup_noheat_listen())
    #await asyncio.sleep(15)
    return group
        
def setup_heat_requests():
    #sensors = []
    #room1_location_sensor = LocationSensor("house/room1/temperature")
    #room1_location_sensor = LocationSensor("outside/temperature")
    #agent = ReflexAgent("room1/user/temp_decrease")
    #agent = ReflexAgent("house/room1/temperature")
    #agent = ReflexAgent("room1/users/get")
    #agent = ReflexAgent("room1/plan/noheating")
    #user = User("house/room1/users/add")
    #sensors.append(room1_location_sensor)
    #sensors.append(agent)
    #sensors.append(room2_location_sensor)
    return gather_heat_requests()
    

async def await_start_simulation():
    pass
  
        
        
if __name__ == "__main__":
    #asyncio.run(await_start_simulation())
    # add sensors
    #heatsetup()
    # make them publish on topics
    print("Disconnected.")
        
    
    