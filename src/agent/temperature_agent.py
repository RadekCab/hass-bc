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
from agent.agents import sem, TIME_INTERVAL
from utils import datetime_to_index, temperature_to_index, index_to_temperature, INTERVAL_SHORTENER
from learning_sim import get_next_temperature_action
from myenum.action import TemperatureAction
from myenum.presence import Presence

LEARNING_CONTACT = "learning11@sure.im"
DUMMY_TEMPERATURE_CONTACT = "simtemperature01@sure.im"
SELF_XMPP = "devices12@sure.im"
DEFAULT_TEMPERATURE = 20


class TemperatureAgent(DeviceAgent):
    """Agent managing room temperature

    Args:
        DeviceAgent class: object providing helpful structure for creating
    agent observing any device
    """

    def __init__(self, devices: list, jid, password, uuid, topic) -> None:
        DeviceAgent.__init__(self, devices, jid, password, uuid, topic)
        self.last_payload = None
        self.temperature_at_interval_start = None
        # self.

    # Spade behavior
    class RecvTemperatureRequestBehav(PeriodicBehaviour):
        async def on_start(self):
            print("Starting receiving behavior . . .")
            pass

        async def run(self):
            temperature = self.get("temperature")
            if temperature is not None and temperature != "nothing":
                msg = Message(to=LEARNING_CONTACT)
                msg.set_metadata("performative", "inform")
                msg.body = "Temperature:" + temperature
                await self.send(msg)
                await self.agent.stop()

    class TemperatureIncUserRequestRecvBehav(PeriodicBehaviour):
        async def run(self):
            if not self.get("receive_from_hass"):
                recv = await self.receive(timeout=5)  # wait for a message for 10 seconds
                if recv:
                    # await asyncio.sleep(2)
                    print("Temp Agent: Notifying model to start heating.")
                    msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
                    msg.set_metadata("performative", "query")
                    msg.body = "Request:temperature_increase"
                    msg.sender = SELF_XMPP
                    self.process_increase_req()
                    # print(str(msg))
                    await self.send(msg)

            else:
                async with sem:
                    await self.activate_mqqt_topic_listening(self.get("mqtt_temperature_increase_topic"))

        async def activate_mqqt_topic_listening(self, topic):
            async with AsyncioPahoClient(str(uuid.uuid4())) as client:
                client._userdata = None
                client.username_pw_set(username="hass", password="nimda")
                _ = await mqtt.listen_to_topic(client, topic)
                await asyncio.sleep(4)
                if client._userdata == "new":
                    self.process_increase_req()

                client.user_data_set("nothing")

        def process_increase_req(self):
            print("Temperature Agent: Received Temperature Increase Request From User.")
            self.set("temperature_inc_req", True)
            inc_counter = self.get("temperature_inc_req_cnt")
            inc_counter += 1
            self.set("temperature_inc_req_cnt", inc_counter)
            print("Temperature Agent: Reflex reaction not implemented. Sending re-learn notification.")

    class TemperatureDecUserRequestRecvBehav(PeriodicBehaviour):
        async def run(self):
            if not self.get("receive_from_hass"):
                recv = await self.receive(timeout=6)  # wait for a message for 10 seconds
                if recv:
                    # await asyncio.sleep(2)
                    print("Temp Agent: Notifying model to stop heating.")

                    msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
                    msg.set_metadata("performative", "query")
                    msg.body = "Request:temperature_decrease"
                    msg.sender = SELF_XMPP
                    self.process_decrease_req()
                    # print(str(msg))
                    await self.send(msg)
            else:
                async with sem:
                    await self.activate_mqqt_topic_listening(self.get("mqtt_temperature_decrease_topic"))

        async def activate_mqqt_topic_listening(self, topic):
            async with AsyncioPahoClient(str(uuid.uuid4())) as client:
                client._userdata = None
                client.username_pw_set(username="hass", password="nimda")
                _ = await mqtt.listen_to_topic(client, topic)
                await asyncio.sleep(5)
                if client._userdata == "new":
                    self.process_decrease_req()

                client.user_data_set("nothing")

        def process_decrease_req(self):
            print("Temperature Agent: Received Temperature Decrease Request From User.")
            self.set("temperature_dec_req", True)
            dec_counter = self.get("temperature_dec_req_cnt")
            dec_counter += 1
            self.set("temperature_dec_req_cnt", dec_counter)
            print("Temperature Agent: Reflex reaction not implemented. Sending re-learn notification.")

    class RecvDummyTemperature(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=5)  # wait for a message for 10 seconds
            if msg:
                msg_arr = msg.body.split(sep=":")
                if msg_arr[0] == "temperature":
                    if msg_arr[1] != "None":
                        # print("Temp. Agent: Temperature From SimReality Received")
                        self.set("temperature", float(msg_arr[1]))
                    else:
                        print("WARN Temp. Agent: [None] From SimReality Received")

    class DummyRequestTemperature(PeriodicBehaviour):
        async def run(self):
            msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
            msg.set_metadata("performative", "query")
            msg.body = "temperature:?"
            await self.send(msg)

    class RoomTemperatureReceiveBehav(PeriodicBehaviour):
        async def on_start(self):
            print("Starting MQTT listening behavior . . .")
            pass

        async def run(self):
            async with sem:
                await self.activate_mqqt_topic_listening(self.get("mqtt_temperature_topic"))

        async def activate_mqqt_topic_listening(self, topic):
            async with AsyncioPahoClient(str(uuid.uuid4())) as client:
                client._userdata = None
                client.username_pw_set(username="hass", password="nimda")
                _ = await mqtt.listen_to_topic(client, topic)
                await asyncio.sleep(4)
                self.set("temperature", client._userdata)
                client.user_data_set("nothing")

    class SendNewTimeIntervalBehav(OneShotBehaviour):
        async def run(self):
            print("Temperature Agent: Notifying DummyTemperature About Time.")
            msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
            msg.set_metadata("performative", "notify")
            msg.body = "time:" + str(self.get("current_time_interval"))
            msg.sender = SELF_XMPP
            await self.send(msg)
            msg.to = "testuser01@sure.im"
            await self.send(msg)

    class RecvLearningRequestsBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=11)  # wait for a message for 10 seconds
            if msg:
                print("Temperature Agent: Received Learning request.")
                temperature = self.get("temperature")

                if temperature is not None and temperature != "nothing" and self.template.body == "temperature":
                    msg = Message(to=LEARNING_CONTACT)  # Instantiate the message
                    msg.set_metadata("performative", "inform")  # Set the "inform" FIPA performative
                    msg.body = "Temperature:" + str(temperature)  # Set the message content
                    msg.sender = SELF_XMPP
                    print("Temperature Agent: Replying...")
                    await self.send(msg)

                elif self.template.body == "temperature":
                    print(
                        "Temperature Agent: cannot send temperature, I dont know it:",
                        temperature,
                    )
                elif self.template.body == "start_heating":
                    await self.agent.start_heating(self)
                elif self.template.body == "stop_heating":
                    await self.agent.stop_heating(self)
                else:
                    print("WARN Temperature Agent: Received unknown message")

    # class RecvTemperatureQueryBehav(CyclicBehaviour):
    #     async def run(self):
    #         recv = await self.receive(timeout=8)  # wait for a message for 10 seconds
    #         if recv:
    #             temperature = self.get("temperature")

    #             if (
    #                 temperature is not None
    #                 and temperature != "nothing"
    #                 and self.template.body == "temperature"
    #             ):
    #                 msg = Message(to=recv.sender)  # Instantiate the message
    #                 msg.set_metadata(
    #                     "performative", "inform"
    #                 )  # Set the "inform" FIPA performative
    #                 msg.body = "Temperature:" + temperature  # Set the message content
    #                 msg.sender = SELF_XMPP
    #                 await self.send(msg)
    #             else:
    #                 print("WARN Temperature Agent: Received unknown message")

    class SolveActionForNewTimeIntervalBehav(OneShotBehaviour):
        async def run(self):
            old_temperature = self.agent.temperature_at_interval_start
            if self.get("temperature") == "nothing":
                print("WARN Temperature Agent: Can't decide next temperature without knowing current one.")
                self.kill()
            if old_temperature == None:
                print("Temperature Agent: Initializing Default Temperature")
                old_temperature = self.get("temperature")
            self.agent.temperature_at_interval_start = self.get("temperature")
            derivative = 0
            if old_temperature > self.get("temperature"):
                derivative = -1
            elif old_temperature < self.get("temperature"):
                derivative = 1

            presence = Presence.PRESENT.value
            time_interval = self.get("current_time_interval")
            temperature = self.get("temperature")
            print(f"Temperature Agent: Current Time Interval {time_interval}, Current Temperature {temperature}, Derivative {derivative}")
            if not os.path.exists("q_table.npy"):
                await asyncio.sleep(30)
            q_table = np.load("q_table.npy")
            print("Temperature Agent: Q-Table Obtained From File")

            action = get_next_temperature_action(
                presence,
                derivative,
                time_interval,
                temperature_to_index(float(temperature)),
                1.0,
                1.0,
                q_table,
            )
            print(
                "Temperature Agent: Next Action Should Be",
                TemperatureAction(action).name,
                ".",
            )
            if TemperatureAction(action).name == "INCREASE":
                await self.agent.start_heating(self)
            elif TemperatureAction(action).name == "DECREASE":
                await self.agent.stop_heating(self)
            await asyncio.sleep(1)

    class NotifyLearningAboutUserIncreaseRequest(OneShotBehaviour):
        async def run(self):
            print("Temperature Agent: Notifying Learning Agent About Request")
            msg = Message(to=LEARNING_CONTACT)
            msg.set_metadata("performative", "notify")
            msg.body = "Request:temperature_increase;" + str(self.get("current_time_interval"))
            msg.sender = SELF_XMPP
            await self.send(msg)

    class NotifyLearningAboutUserDecreaseRequest(OneShotBehaviour):
        async def run(self):
            print("Temperature Agent: Notifying Learning Agent About Request")
            msg = Message(to=LEARNING_CONTACT)
            msg.set_metadata("performative", "notify")
            msg.body = "Request:temperature_decrease;" + str(self.get("current_time_interval"))
            msg.sender = SELF_XMPP
            await self.send(msg)

    class SimTimeIntervalCheckBehav(PeriodicBehaviour):
        async def run(self):
            # sim increments are shorter
            if self.get("time") == "sim":
                index = datetime_to_index()
                new_interval = False
                print("Time:", str(timedelta(minutes=int(self.get("current_time_interval")) * 15)), "(", index, ")")
                if index != self.get("current_time_interval"):
                    new_interval = True
                self.set("current_time_interval", index)
                if new_interval or self.get("start_interval"):
                    if self.get("start_interval"):
                        # Delay At Start
                        await asyncio.sleep(13)
                    self.set("temperature_inc_req_cnt", 0)
                    self.set("temperature_dec_req_cnt", 0)
                    print("Temperature Agent: Solving new time interval state and action...")
                    self.set("start_interval", False)
                    dummy_notif_b = self.agent.SendNewTimeIntervalBehav()
                    b = self.agent.SolveActionForNewTimeIntervalBehav()
                    self.agent.add_behaviour(b)
                    self.agent.add_behaviour(dummy_notif_b)

    class ParameterSelfCheckBehav(PeriodicBehaviour):
        async def run(self):
            reload_plan = True
            duplicate_print_inc = True
            duplicate_print_dec = True
            if (os.path.exists("qtable.bin")) and reload_plan:
                reload_plan = False
            inc_counter = self.get("temperature_inc_req_cnt")
            dec_counter = self.get("temperature_dec_req_cnt")

            if self.get("temperature_inc_req") and int(inc_counter) <= 1:
                self.agent.add_behaviour(self.agent.notify_temperature_increase_behav)
                self.set("temperature_inc_req", False)
                duplicate_print_inc = True
            elif self.get("temperature_inc_req") and int(inc_counter) > 1 and duplicate_print_inc:
                duplicate_print_inc = False
            if self.get("temperature_dec_req") and int(dec_counter) <= 1:
                self.agent.add_behaviour(self.agent.notify_temperature_decrease_behav)
                self.set("temperature_dec_req", False)
                duplicate_print_dec = True
            elif self.get("temperature_dec_req") and int(dec_counter) > 1 and duplicate_print_dec:
                duplicate_print_dec = False

    async def setup(self):
        print("Temperature agent started.")
        self.set("current_time_interval", datetime_to_index())
        self.set("start_interval", True)
        self.set("temperature_inc_req_cnt", 0)
        self.set("temperature_dec_req_cnt", 0)

        template_learning_temperature = Template()
        template_learning_temperature.metadata = {"performative": "query"}
        template_learning_temperature.body = "temperature"
        template_learning_temperature.sender = LEARNING_CONTACT

        template_learning_heating = Template()
        template_learning_heating.metadata = {"performative": "query"}
        template_learning_heating.body = "start_heating"
        template_learning_heating.sender = LEARNING_CONTACT

        template_learning_stopheat = Template()
        template_learning_stopheat.metadata = {"performative": "query"}
        template_learning_stopheat.body = "stop_heating"
        template_learning_stopheat.sender = LEARNING_CONTACT

        template_dummy_reality = Template()
        template_dummy_reality.metadata = {"performative": "inform"}
        template_dummy_reality.sender = DUMMY_TEMPERATURE_CONTACT

        template_dummy_inc_user_req = Template()
        template_dummy_inc_user_req.metadata = {"performative": "notify"}
        template_dummy_inc_user_req.sender = "testuser01@sure.im"
        template_dummy_inc_user_req.body = "temperature:increase"

        template_dummy_dec_user_req = Template()
        template_dummy_dec_user_req.metadata = {"performative": "notify"}
        template_dummy_dec_user_req.sender = "testuser01@sure.im"
        template_dummy_dec_user_req.body = "temperature:decrease"

        recv_learning_heating_request_behav = self.RecvLearningRequestsBehav()
        recv_learning_stopheat_request_behav = self.RecvLearningRequestsBehav()
        recv_learning_temp_request_behav = self.RecvLearningRequestsBehav()
        periodic_parameter_check_behav = self.ParameterSelfCheckBehav(period=10)
        time_interval_behav = self.SimTimeIntervalCheckBehav(period=3)
        process_new_time_interval_behav = self.SolveActionForNewTimeIntervalBehav()
        self.next_action_behav = process_new_time_interval_behav

        self.notify_temperature_increase_behav = self.NotifyLearningAboutUserIncreaseRequest()
        self.notify_temperature_decrease_behav = self.NotifyLearningAboutUserDecreaseRequest()

        if self.get("receive_from_hass"):
            self.add_behaviour(self.RoomTemperatureReceiveBehav(period=10))
            self.add_behaviour(self.TemperatureIncUserRequestRecvBehav(period=4))
            self.add_behaviour(self.TemperatureDecUserRequestRecvBehav(period=5))
        else:
            self.set("temperature", DEFAULT_TEMPERATURE)
            self.add_behaviour(self.RecvDummyTemperature(), template_dummy_reality)
            self.add_behaviour(
                self.TemperatureDecUserRequestRecvBehav(period=4),
                template_dummy_dec_user_req,
            )
            self.add_behaviour(
                self.TemperatureIncUserRequestRecvBehav(period=5),
                template_dummy_inc_user_req,
            )
            self.add_behaviour(self.DummyRequestTemperature(period=20))

        self.add_behaviour(recv_learning_temp_request_behav, template_learning_temperature)
        self.add_behaviour(recv_learning_heating_request_behav, template_learning_heating)
        self.add_behaviour(recv_learning_stopheat_request_behav, template_learning_stopheat)
        self.add_behaviour(periodic_parameter_check_behav)
        self.add_behaviour(time_interval_behav)

    async def start_heating(self, behaviour):
        msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
        msg.set_metadata("performative", "notify")
        msg.body = "Request:temperature_increase"
        msg.sender = SELF_XMPP
        await behaviour.send(msg)
        await asyncio.sleep(1)
        async with AsyncioPahoClient(str(uuid.uuid4())) as client:
            print("Starting heating...")
            client.user_data_set('{"action":true}')
            topic = self.get("mqtt_thermostat_topic")
            client.username_pw_set(username="hass", password="nimda")
            _ = await mqtt.publish_to_topic(client, topic + "/set")
            await asyncio.sleep(8)
            client.user_data_set("nothing")

    async def stop_heating(self, behaviour):
        msg = Message(to=DUMMY_TEMPERATURE_CONTACT)
        msg.set_metadata("performative", "notify")
        msg.body = "Request:temperature_decrease"
        msg.sender = SELF_XMPP
        await behaviour.send(msg)
        await asyncio.sleep(1)
        async with AsyncioPahoClient(str(uuid.uuid4())) as client:
            print("Stopping heating...")
            client.user_data_set('{"action":false}')
            topic = self.get("mqtt_thermostat_topic")
            client.username_pw_set(username="hass", password="nimda")
            _ = await mqtt.publish_to_topic(client, topic + "/set")
            await asyncio.sleep(8)
            client.user_data_set("nothing")
