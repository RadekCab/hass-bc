import asyncio
import uuid
import time
import spade
import sys, getopt
from asyncio_paho import AsyncioPahoClient

import utils
import mqtt
from sensors import LocationSensor, TemperatureSensor
from sensors import Sensor
from agent.agents import ReflexAgent
from agent.temperature_agent import TemperatureAgent
from agent.learning_agent import LearningAgent
from agent.userinfo_agent import UserAgent
from user import User


async def connect_to_topic(sensor):
    response = ""
    # for sensor in sensors:
    async with AsyncioPahoClient(str(sensor.uuid)) as client:
        print(sensor.get_topic())
        client.username_pw_set(username="hass", password="nimda")

        response = await mqtt.listen_to_topic(client, sensor.get_topic())
        await asyncio.sleep(3)

        print(
            f"RESPONSE INSIDE MAIN LOOP {client._userdata} RECEIVED BY {client._client_id}"
        )
        response = client._userdata

    return response


async def publish_to_topic(sensor):
    response = ""

    async with AsyncioPahoClient(str(sensor.uuid)) as client:
        print(sensor.get_topic())
        client.username_pw_set(username="hass", password="nimda")

        response = await mqtt.publish_to_topic(client, sensor.get_topic())
        await asyncio.sleep(3)
        print(
            f"RESPONSE INSIDE MAIN LOOP {client._userdata} RECEIVED BY {client._client_id}"
        )
        response = client._userdata

    return response


async def get_requests_by_time(seconds: int, topic: str, sensor):
    """
    returns 2d array, first axis = heating requests, second axis = stop heating requests

    """
    ret_arr = []
    t_end = time.time() + seconds
    while time.time() < t_end:
        payload = await connect_to_topic(sensor)
        await asyncio.sleep(2)
        if str(payload) != "nothing":
            ret_arr.append(payload)
    return ret_arr


async def setup_noheat_listen():
    agent1 = ReflexAgent("room1/plan/noheating")

    return await get_requests_by_time(14, agent1.get_topic, agent1)


async def setup_heating_listen():
    await asyncio.sleep(2)

    agent2 = ReflexAgent("room1/plan/heating")

    return await get_requests_by_time(28, agent2.get_topic, agent2)


async def setup_start_sim_listen():
    agent = ReflexAgent("hass/start_sim")
    return await get_requests_by_time(10, agent.get_topic, agent)


async def gather_heat_requests():
    group = await asyncio.gather(setup_heating_listen(), setup_noheat_listen())
    return group


def setup_heat_requests():
    return gather_heat_requests()


async def set_room_temperature_from_mqtt(room: str, temperature: int):
    # sensors real/fake should only publish here
    agent = TemperatureSensor(f"house/{room}/temperature")
    agent.set_temperature(temperature)
    await publish_to_topic(agent)
    await asyncio.sleep(4)
    print(f"Published new temperature {temperature}...")


async def set_default_temperature(temperature):
    await set_room_temperature_from_mqtt("room1", temperature)


async def simulation_start():
    is_started = await setup_start_sim_listen()
    await asyncio.sleep(11)
    if is_started:
        print(is_started)


async def setup_agents(mode):
    """Used for simulation setup

    Args:
        mode (_type_): real or sim, while sim missing experimental
                        temperature setting phase
                        both use same time in the end
                        for better time interval uderstaning
    """
    jid = "devices12@sure.im"
    pw = "devices66"
    agent_id = uuid.uuid4()

    utils.INTERVAL_SHORTENER = 1
    temperature_agent = TemperatureAgent(
        [], jid, pw, agent_id, "house/agents/temperature"
    )
    temperature_agent.set("uuid", agent_id)
    temperature_agent.set("mqtt_temperature_topic", "house/room1/temperature")
    temperature_agent.set("mqtt_thermostat_topic", "house/room1/thermostat")
    temperature_agent.set(
        "mqtt_temperature_increase_topic", "house/room1/user/temp_increase"
    )
    temperature_agent.set(
        "mqtt_temperature_decrease_topic", "house/room1/user/temp_decrease"
    )
    temperature_agent.set("temperature", None)
    temperature_agent.set("time", mode)

    # temperature starts heating
    # so activate fake temperature change simulation through topic
    # and automation that changes temp. in time

    learning_agent = LearningAgent("learning11@sure.im", "learning66")
    learning_agent.set("init", False)
    if mode == "real":
        learning_agent.set("init", True)
    learning_agent.set(
        "heating_requests",
        {0: "15.5", 1: "15.5", 2: "16.0", 3: "16.5", 4: "16.5", 5: "17.0"},
    )
    learning_agent.set(
        "stopheat_requests",
        {0: "17.0", 1: "16.5", 2: "16.5", 3: "16.0", 4: "16.0", 5: "15.5"},
    )
    learning_agent.set("learning", True)
    learning_agent.set("init_complete", True)
    learning_agent.set("timeplan_heat", None)
    learning_agent.set("timeplan_noheat", None)

    # learning agent receives the plan from user agent

    # FROM UI
    # - start learning after plan obtaining, with temperature
    # and user model being built
    # learning notifies it about new plan

    user_agent = UserAgent([], topic="house/agents/user")
    user_agent.set("mqtt_timeplan_heat_topic", "room1/plan/heating")
    user_agent.set("mqtt_timeplan_noheat_topic", "room1/plan/noheating")

    await temperature_agent.start(False)
    await user_agent.start(False)
    await learning_agent.start(False)
    print("Agents Started")
    await spade.wait_until_finished(temperature_agent)
    await spade.wait_until_finished(learning_agent)
    await spade.wait_until_finished(user_agent)


if __name__ == "__main__":
    argv = sys.argv[1:]
    mode = "sim"
    opts, args = getopt.getopt(argv, "m:", ["mode="])
    for opt, arg in opts:
        if opt in ("-m", "--mode"):
            if arg == "sim" or arg == "real":
                mode = arg
            else:
                print("WARN Unknown Command Line Parameter.", arg)
                mode = "sim"
    spade.run(setup_agents(mode))
    print("Disconnected.")
