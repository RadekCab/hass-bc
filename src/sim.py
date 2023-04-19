import asyncio
import uuid
import utils
from asyncio_paho import AsyncioPahoClient
from sensors import LocationSensor

async def publish_loop(sensors : list):
    async def on_connect_async(client, userdata, flags_dict, result):
        print("Connected.")
        print(flags_dict)
        nonlocal topic
        await client.subscribe(topic, 1)
        #client.subscribe("fakedevice/get")
    
    async def on_message_async(client, userdata, msg):
        print(f"My message: topic: {msg.topic}: payload: {str(msg.payload)}, qos; {str(msg.qos)}, reatain flag: {str(msg.retain)} Temp: {userdata}")
        
    async def on_connect_fail(client):
        print("connection failed")
        
    async def on_subscribe(client, userdata, mid, granted_qos):
        print("Subscribed!")   
        print(f"mid: {str(mid)}, data: {str(userdata)}")
        nonlocal topic
        print("DEBUG: pulishing on topic = ", topic)
        client.publish(topic, userdata)
        
    async def on_publish(client, userdata, result):
        print("Now temperature should be set")
        print(f"result: {str(result)}")
    
    broker = "127.0.0.1"
    port = 1883
    # TODO
    # sekvencne, to nechceme
    # lepsi format json dat
    for sensor in sensors:  
        async with AsyncioPahoClient(str(sensor.uuid)) as client:
            topic = sensor.get_topic()
            client.username_pw_set(username="hass",password="nimda")
            client.asyncio_listeners.add_on_connect(on_connect_async)
            client.asyncio_listeners.add_on_connect_fail(on_connect_fail)
            client.asyncio_listeners.add_on_message(on_message_async)
            client.asyncio_listeners.add_on_subscribe(on_subscribe)
            client.asyncio_listeners.add_on_publish(on_publish)
            await client.asyncio_connect(broker, port=port, keepalive=60)
            client.user_data_set(utils.get_json_payload(sensor))
            #client.user_data_set(19)
            await asyncio.sleep(3)
    
    
        
def setup():
    sensors = []
    room1_location_sensor = LocationSensor("house/room1/location/set")
    #room2_location_sensor = LocationSensor("house/room2/location/set")
    sensors.append(room1_location_sensor)
    #sensors.append(room2_location_sensor)
    asyncio.run(publish_loop(sensors))
  
        
        
if __name__ == "__main__":
    # add sensors
    setup()
    # make them publish on topics
    print("Disconnected.")
        
    
    