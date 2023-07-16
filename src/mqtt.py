import asyncio
import uuid
import time
from utils import Observable
from asyncio_paho import AsyncioPahoClient
from sensors import LocationSensor
from sensors import Sensor
from agent.agents import ReflexAgent
from user import User



class Setting():
    def __init__(self, topic):
        self.TOPIC = topic
        self.BROKER = "127.0.0.1"
        self.PORT = 1883
        self.response = "No response"

setup = None

async def on_connect_async_listen(client, userdata, flags_dict, result):
    global setup
    print("Trying to subscribe to topic.", setup.TOPIC)
    print("flags:", flags_dict)
    # agent wants to get data
    # TODO jenom subscribe a nastavit v mqtt.yaml
    await client.subscribe(setup.TOPIC, 1)
    #await client.publish(TOPIC+"/get", 1)
    #await asyncio.sleep(.5)
    #client.subscribe("fakedevice/get")
        
async def on_connect_async_publish(client, userdata, flags_dict, result):
    global setup
    print("Trying to subscribe to topic.", setup.TOPIC)
    print("flags:", flags_dict)
    # agents wants to set data or
    # fake sensor sets data
    await client.publish(setup.TOPIC+"/set", 1)   
    #await asyncio.sleep(.5)
    #client.subscribe("fakedevice/get")
    
async def on_message_async(client : AsyncioPahoClient, userdata, msg):
    print(f"RECEIVED: topic: {msg.topic}: payload: {str(msg.payload)}, qos; {str(msg.qos)}, reatain flag: {str(msg.retain)}")
    #setting.response = msg.payload.decode("utf-8")
    
    client.user_data_set(msg.payload.decode("utf-8"))
    #print(str(msg.payload.decode("utf-8")))
        
        
async def on_connect_fail(client):
    print("connection failed")
        
async def on_subscribe(client, userdata, mid, granted_qos):
    print("Subscribed!")   
    print(f"mid: {str(mid)}, userdata: {str(userdata)}")
    #client.publish(topic, userdata)
        
async def on_publish(client, userdata, result):
    print("Published.")
    # TODO CO ZNAMENA 2
    print(f"publish response: {str(result)}")

async def listen_to_topic(client : AsyncioPahoClient, topic : str):
    global setup
    setup = Setting(topic)
    setup.TOPIC = topic
    custom = "nothing"
    client.user_data_set(custom)
    client.asyncio_listeners.add_on_connect(on_connect_async_listen)
    client.asyncio_listeners.add_on_connect_fail(on_connect_fail)
    client.asyncio_listeners.add_on_subscribe(on_subscribe)
    client.asyncio_listeners.add_on_publish(on_publish)
    client.asyncio_listeners.add_on_message(on_message_async)
    await client.asyncio_connect(setup.BROKER, port=setup.PORT, keepalive=60)
    return custom
    # if (setup.response != "No response"): 
    #     return setup.response
    # try:
    #     while True:
    #         if (setup.response != "No response"): 
    #             return setup.response
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Stopping...")
    
    #response = Observable()(client.asyncio_listeners.add_on_message(on_message_async))
    

async def publish_to_topic(client : AsyncioPahoClient, topic : str):
    global setup
    setup = Setting(topic)
    setup.TOPIC = topic
    client.asyncio_listeners.add_on_connect(on_connect_async_publish)
    client.asyncio_listeners.add_on_connect_fail(on_connect_fail)
    client.asyncio_listeners.add_on_message(on_message_async)
    client.asyncio_listeners.add_on_subscribe(on_subscribe)
    client.asyncio_listeners.add_on_publish(on_publish)
    await client.asyncio_connect(setup.BROKER, port=setup.PORT, keepalive=60)
    # TODO doesnt work, use future?
    return setup.response
