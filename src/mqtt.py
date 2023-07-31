from asyncio_paho import AsyncioPahoClient


class Setting:
    def __init__(self, topic):
        self.TOPIC = topic
        self.BROKER = "127.0.0.1"
        self.PORT = 1883
        self.response = "No response"


setup = None


async def on_connect_async_listen(client, userdata, flags_dict, result):
    global setup

    # agent wants to get data
    await client.subscribe(setup.TOPIC, 0)
    # await client.publish(TOPIC+"/get", 1)
    # await asyncio.sleep(.5)
    # client.subscribe("fakedevice/get")


async def on_connect_async_publish(client, userdata, flags_dict, result):
    global setup
    await client.publish(setup.TOPIC, userdata, retain=False)


async def on_message_async(client: AsyncioPahoClient, userdata, msg):
    received_payload = msg.payload.decode("utf-8")
    if received_payload == "":
        client.user_data_set("Empty response.")
    else:
        client.user_data_set(received_payload)
    msg = None


async def on_connect_fail(client):
    print("MQTT: connection failed")


async def on_subscribe(client, userdata, mid, granted_qos):
    pass


async def on_publish(client, userdata, result):
    pass


async def listen_to_topic(client: AsyncioPahoClient, topic: str):
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


async def publish_to_topic(client: AsyncioPahoClient, topic: str):
    global setup
    setup = Setting(topic)
    setup.TOPIC = topic
    client.asyncio_listeners.add_on_connect(on_connect_async_publish)
    client.asyncio_listeners.add_on_connect_fail(on_connect_fail)
    client.asyncio_listeners.add_on_message(on_message_async)
    client.asyncio_listeners.add_on_subscribe(on_subscribe)
    client.asyncio_listeners.add_on_publish(on_publish)
    await client.asyncio_connect(setup.BROKER, port=setup.PORT, keepalive=60)

    return setup.response
