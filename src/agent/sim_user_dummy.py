import asyncio
import uuid
import spade
import numpy as np
import os.path
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.template import Template
from spade.message import Message
from asyncio_paho import AsyncioPahoClient
from datetime import datetime, timedelta

import mqtt
from agent.device_agent import DeviceAgent
from agent.agents import sem2, TIME_INTERVAL
from utils import datetime_to_index, temperature_to_index, index_to_temperature, INTERVAL_SHORTENER, time_index_to_seconds
from learning_sim import get_next_temperature_action
from myenum.action import TemperatureAction
from myenum.presence import Presence
from sim_user import SimUser

TEMPERATURE_CONTACT = "devices12@sure.im"
SELF_XMPP = "testuser01@sure.im"
DEFAULT_TEMP = 20


class SimUserAgent(DeviceAgent):
    """Agent simulating user
    - automatizovany uzivatel (jako v learningu)
    ALE reagujici na realny system se stats zaznamenanymi pozadavky

        # TODO process user requests to graph

    Args:
        DeviceAgent class: object providing helpful structure for creating
    agent observing any device
    """

    def __init__(self, jid, pw, heat_at: list, noheat_at: list) -> None:
        DeviceAgent.__init__(self, [], jid, pw, uuid.uuid4(), "")
        # for default temperature of 20
        self.heat_start_goal = heat_at
        self.noheat_start_goal = noheat_at
        self.sensitivity = 2
        # super().__init__()

    # class CheckTemperatureBehav(PeriodicBehaviour):
    #     async def run(self):
    #         msg = Message(to=TEMPERATURE_CONTACT, sender=SELF_XMPP, body="temperature")  # Set the message content
    #         msg.set_metadata("performative", "query")
    #         await self.send(msg)
    #         print("User Dummy: Let me feel the temperature!")

    class SendRequestsBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(to=TEMPERATURE_CONTACT)  # Instantiate the message
            msg.set_metadata("performative", "notify")
            msg.sender = SELF_XMPP
            request = self.get("request")
            if request == TemperatureAction.INCREASE:
                msg.body = "temperature:increase"  # Set the message content
            elif request == TemperatureAction.DECREASE:
                msg.body = "temperature:decrease"  # Set the message content
            await self.send(msg)
            async with sem2:
                with open("requests.csv", "a") as f:
                    # now = datetime.now()
                    f.write(str(time_index_to_seconds(int(self.get("current_time_interval")))) + ";" + str(request.value) + ";\n")
            print(f"Dummy user, sent {str(request)} request to temperature agent.")

    class SimTimeIntervalCheckBehav(PeriodicBehaviour):
        async def run(self):
            # sim increments are shorter
            if self.get("time") == "sim":
                index = datetime_to_index()
                new_interval = False
                if index != self.get("current_time_interval"):
                    new_interval = True
                # self.set("current_time_interval", index)
                if new_interval:
                    pass

    class ProcessTemperatureForNextTimeIndexBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                msg_arr = msg.body.split(sep=":")
                if msg_arr[0] == "time":
                    print("User. Model: Time index change notification received.")
                    time_index = msg_arr[1]
                    self.set("current_time_interval", int(time_index))

    class ParameterSelfCheckBehav(PeriodicBehaviour):
        async def run(self):
            # TODO present time

            if np.random.random() < 0.5:
                # if True # TODO get current temperature from file != target
                temperature = None
                if os.path.exists("temperature_model.csv"):
                    async with sem2:
                        with open("temperature_model.csv", "r") as f:
                            temperature = str(f.read()).split(sep=";")[0]
                    await asyncio.sleep(2)
                    if temperature is not None:
                        self.set("current_temperature", float(temperature))
                    user_self = self.get("self")
                    if self.get("current_time_interval") != None:
                        curr_time = int(self.get("current_time_interval"))
                        curr_temp = temperature_to_index(self.get("current_temperature"))

                        request = user_self.get_user_request_per_timeframe(
                            curr_time,
                            curr_temp,
                        )
                        # dont send requests repeatedly, TODO change?
                        last_complain_time = -1
                        last_complain_temp = -1
                        if self.get("last_complain_time") is not None:
                            last_complain_time = int(self.get("last_complain_time"))
                        if self.get("last_complain_temp") is not None:
                            last_complain_temp = int(self.get("last_complain_temp"))
                        if request is not None:
                            self.set("request", request)
                            b = self.agent.SendRequestsBehav()
                            self.agent.add_behaviour(b)
                            self.set("last_complain_temp", curr_temp)
                            self.set("last_complain_time", curr_time)
                        # elif request is not None:
                        # TODO solve duplication later
                        # if request is not None and last_complain_temp != curr_temp and last_complain_time != curr_time and last_complain_time != -1:
                        #     self.set("request", request)
                        #     b = self.agent.SendRequestsBehav()
                        #     self.agent.add_behaviour(b)
                        #     self.set("last_complain_temp", curr_temp)
                        #     self.set("last_complain_time", curr_time)
                        # elif request is not None:
                        #     print("Dummy User: Unhappy but silent this time.")

    async def setup(self):
        print("User started.")
        InhabitantSelf = SimUser("user1", leave=[10], arrive=[13])
        InhabitantSelf.process_temperature_targets_from_intervals(DEFAULT_TEMP, self.heat_start_goal, self.noheat_start_goal)
        self.set("self", InhabitantSelf)
        self.set("current_temperature", None)
        self.set("current_time_interval", datetime_to_index())
        self.set("last_complain_temp", None)
        self.set("last_complain_time", None)
        # self.set("current_time_interval", datetime_to_index())
        # self.set("start_interval", True)
        # self.set("temperature_inc_req_cnt", 0)

        template_temperature_recv = Template()
        template_temperature_recv.metadata = {"performative": "inform"}
        template_temperature_recv.sender = TEMPERATURE_CONTACT

        template_time_notif = Template()
        template_time_notif.metadata = {"performative": "notify"}
        template_time_notif.sender = "devices12@sure.im"

        # self.add_behaviour(self.RoomTemperatureReceiveBehav(period=10))
        # self.add_behaviour(self.CheckTemperatureBehav(period=8))
        self.add_behaviour(self.SimTimeIntervalCheckBehav(period=5))
        self.add_behaviour(self.ParameterSelfCheckBehav(period=10))
        self.add_behaviour(self.ProcessTemperatureForNextTimeIndexBehav(), template_time_notif)

    async def mqtt_req_heating(self):
        # async with AsyncioPahoClient(str(uuid.uuid4())) as client:
        #     print("Starting heating...")
        #     client.user_data_set('{"action":true}')
        #     topic = self.get("mqtt_thermostat_topic")
        #     client.username_pw_set(username="hass", password="nimda")
        #     _ = await mqtt.publish_to_topic(client, topic + "/set")
        #     await asyncio.sleep(8)
        #     client.user_data_set("nothing")
        pass

    async def mqtt_req_noheating(self):
        # async with AsyncioPahoClient(str(uuid.uuid4())) as client:
        #     print("Stopping heating...")
        #     client.user_data_set('{"action":false}')
        #     topic = self.get("mqtt_thermostat_topic")
        #     client.username_pw_set(username="hass", password="nimda")
        #     _ = await mqtt.publish_to_topic(client, topic + "/set")
        #     await asyncio.sleep(8)
        #     client.user_data_set("nothing")
        pass
