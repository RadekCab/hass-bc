import asyncio
import uuid
import spade
import os.path
import numpy as np
import matplotlib.pyplot as plt
import random
from spade.agent import Agent as SpadeAgent
from spade.behaviour import CyclicBehaviour, PeriodicBehaviour, OneShotBehaviour
from spade.template import Template
from spade.message import Message
from asyncio_paho import AsyncioPahoClient

from datetime import datetime, timedelta

from agent.agents import sem2
from agent.device_agent import DeviceAgent
from agent.agents import sem, TIME_INTERVAL
from utils import datetime_to_index, temperature_to_index, index_to_temperature, time_index_to_seconds, smoothen, INTERVAL_SHORTENER
from learning_sim import get_next_temperature_action
from myenum.action import TemperatureAction
from myenum.presence import Presence
from sim_temperature import SimTemperature

SELF_XMPP = "simtemperature01@sure.im"
DEFAULT_TEMP = 20


class SimTemperatureAgent(SpadeAgent):
    """Agent simulating real temperature
    - saves temperature to file

    # TODO ten timeplan with top priority
        - timeplan beofre a after ? z obrazku promyslet
    # TODO aplikovat multiplier na real časy nebo modifikovat
    # vteřiny při zpracování do grafů

    # TODO try to do smooth temperatures here for every second idk
    # TODO user requests jinak vykreslit

    # TODO otocit a formatovat grafy

    Args:
        DeviceAgent class: object providing helpful structure for creating
    agent observing any device
    """

    data_heat = []
    data_temp = []
    # start_time = None
    # end_time = None
    heating_speed = random.randint(5, 10)
    steps = 6

    class ProcessTemperatureForNextTimeIndexBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message for 10 seconds
            if msg:
                msg_arr = msg.body.split(sep=":")
                if msg_arr[0] == "time":
                    print("Temp. Model: Time index change notification received.")

                    time_index = msg_arr[1]
                    if self.agent.start_time is None:
                        self.agent.start_time = time_index_to_seconds(int(time_index))
                        self.set("last_time_index", time_index)
                        print(f"======== Temp. Model: Start Time Set {self.agent.start_time} ({time_index}). =========")

                    step = int(time_index) - int(self.get("last_time_index"))
                    if step > 5:
                        self.set("temp_step", 5)
                    elif step < 0:
                        self.set("temp_step", 0)
                    else:
                        new_step = int(self.get("temp_step") + 1)
                        self.set("temp_step", new_step)
                        if new_step == 6:
                            self.set("temp_step", 5)
                    print("Temp. Model: Temperature Enhance Delta:", self.get("temp_step"))
                    self.set("last_time_index", int(time_index))
                    if self.get("heat_flag") or self.get("noheat_flag"):
                        # if new_interval_heating:
                        print("Temp model: Changing temperature (result of last 15min no/heating)")
                        self.agent.add_behaviour(self.agent.HeatingSelfCheckBehav())
                        # new_interval_heating = False
                        await asyncio.sleep(2)
                    await self.agent.process_temperature()
                    await asyncio.sleep(1)
                print("Temp. Model: Received Time Related Message.")

    class RecvAndSendTemperatureBehav(CyclicBehaviour):
        async def run(self):
            recv = await self.receive(timeout=5)  # wait for a message for 10 seconds
            if recv:
                recv_arr = recv.body.split(sep=":")
                if recv_arr[0] == "temperature":
                    mes = Message(
                        to=str(recv.sender),
                        sender=SELF_XMPP,
                        body="temperature:" + str(self.get("current_temp")),
                    )  # Set the message content
                    mes.set_metadata("performative", "inform")
                    await self.send(mes)
                # msg.body = "Request:temperature_increase"
                elif recv_arr[0] == "Request":
                    print("Temp. Model: Received new temperature change request.")
                    new_temperature_index = None
                    heat_flag = self.get("heat_flag")
                    noheat_flag = self.get("noheat_flag")
                    # TODO if new interval
                    if recv_arr[1] == "temperature_increase":
                        # intensity increase only at new time intetrval (return here)
                        if heat_flag:
                            return
                        if noheat_flag:
                            self.set("temp_step", 0)
                        self.set("heat_flag", True)
                        self.set("noheat_flag", False)
                        if self.get("heating_process_over"):
                            # print("Temp Model: Starting temperature heat calculation behaviour.")
                            self.agent.add_behaviour(self.agent.HeatingSelfCheckBehav())
                    elif recv_arr[1] == "temperature_decrease":
                        if noheat_flag:
                            return
                        if heat_flag:
                            self.set("temp_step", 0)
                        self.set("noheat_flag", True)
                        self.set("heat_flag", False)
                        if self.get("heating_process_over"):
                            # print("Temp Model: Starting temperature cooling calculation behaviour.")
                            self.agent.add_behaviour(self.agent.HeatingSelfCheckBehav())

    class HeatBehav(OneShotBehaviour):
        async def run(self):
            state = self.get("state")
            current_temp = self.get("current_temp")
            new_temperature_index = temperature_to_index(float(current_temp))
            if state == TemperatureAction.KEEP.value or state == TemperatureAction.DECREASE.value:
                # print("Temp Model: Heating...")
                self.set("temp_step", 0)
            self.set("state", TemperatureAction.INCREASE.value)
            temp_step = self.get("temp_step")
            model = self.get("self")
            # rare duplication prevented
            if temp_step > 5:
                temp_step = 5
            new_temperature_index = temperature_to_index(model.next_temperature(current_temp, temp_step))
            print("Temp Model: (+) Intesity...", str(temp_step))
            self.set("temp_step", temp_step + 1)
            self.set("current_temp", index_to_temperature(new_temperature_index))
            async with sem2:
                with open("temperature_model.csv", "w") as f:
                    f.write(f"{str(index_to_temperature(new_temperature_index))};")
            self.kill()

    class NoheatBehav(OneShotBehaviour):
        async def run(self):
            current_temp = self.get("current_temp")
            new_temperature_index = temperature_to_index(float(current_temp))
            state = self.get("state")
            if state == TemperatureAction.KEEP.value or state == TemperatureAction.INCREASE.value:
                self.set("temp_step", 0)
            self.set("state", TemperatureAction.DECREASE.value)
            temp_step = self.get("temp_step")
            model = self.get("self")
            # rare duplication prevented
            if temp_step > 5:
                temp_step = 5
            new_temperature_index = temperature_to_index(model.next_temperature(current_temp, temp_step, is_decrease=True))
            print("Temp Model: (-) Intesity...", str(temp_step))
            self.set("temp_step", temp_step + 1)
            self.set("current_temp", index_to_temperature(new_temperature_index))
            async with sem2:
                with open("temperature_model.csv", "w") as f:
                    f.write(f"{str(index_to_temperature(new_temperature_index))};")
            self.kill()

    class DataCollectTimer(OneShotBehaviour):
        async def run(self):
            # TODO multiply
            recv = await self.receive(timeout=60 * 3)  # TODO dynamic sim length
            if recv is None:
                self.set("data_collection_running", False)

    class ParameterSelfCheckBehav(PeriodicBehaviour):
        async def run(self):
            if not self.get("data_collection_running"):
                self.set("data_collection_running", True)
                await self.agent.show_temps_and_heating()

    class HeatingSelfCheckBehav(OneShotBehaviour):
        async def run(self):
            if int(self.get("temp_step")) < self.agent.steps:
                self.set("heating_process_over", False)
                # for i in range(self.agent.steps):
                if self.get("heat_flag"):
                    print("Temp. Model: Starting Heating with intensity", self.get("temp_step"))
                    b = self.agent.HeatBehav()
                    self.agent.add_behaviour(b)
                    await b.join()
                    # await asyncio.sleep(self.agent.heating_speed)

                elif self.get("noheat_flag"):
                    print("Temp. Model: Starting Cooling down with intensity", self.get("temp_step"))
                    b = self.agent.NoheatBehav()
                    self.agent.add_behaviour(b)
                    await b.join()
                    # await asyncio.sleep(self.agent.heating_speed)
                else:
                    print("WARN Temp Model: Heating/Cooling not yet set.")
                    # break
                self.set("heating_process_over", True)

    class DataCollectBehav(PeriodicBehaviour):
        async def run(self):
            # now = datetime.now().second
            self.agent.data_temp.append(float(self.get("current_temp")))
            if self.get("state") == TemperatureAction.INCREASE.value:
                self.agent.data_heat.append(TemperatureAction.INCREASE.value)
            else:
                self.agent.data_heat.append(TemperatureAction.DECREASE.value)

    async def setup(self):
        # now = datetime.now()  # experiment
        # self.start_time = (now.hour * 3600 + now.minute * 60 + now.second) * INTERVAL_SHORTENER
        self.start_time = None
        # print("Temp. model started. Setting Start Time", self.start_time, "should be (speed up) index: ", datetime_to_index())
        print("Temp. model started.")
        heat_temperatures = [20, 20.5, 21, 21, 21.5, 22]
        stop_temperatures = [20, 20, 19.5, 19.5, 19, 19]
        after_actions = heat_temperatures
        after_actions = np.vstack((after_actions, stop_temperatures))
        self.set("self", SimTemperature(20, after_actions, exp_init=True))
        self.set("state", TemperatureAction.KEEP.value)
        self.set("temp_step", 0)
        self.set("current_temp", DEFAULT_TEMP)
        self.set("data_collection_running", True)
        self.set("heating_process_over", True)
        self.set("last_time_index", None)
        # self.set("last_time_index", int(datetime_to_index(self.start_time % 95)))

        # self.set("current_time_interval", datetime_to_index())
        # self.set("start_interval", True)
        # self.set("temperature_inc_req_cnt", 0)

        # self.NoheatBehav().set_agent(self)
        # self.HeatBehav().set_agent(self)
        self.noheatBehav = self.NoheatBehav()
        self.heatBehav = self.HeatBehav()
        # self.HeatingSelfCheckBehav().set_agent(self)

        self.heatCheckBehav = self.HeatingSelfCheckBehav()
        # template_learning_temperature = Template()
        # template_learning_temperature.metadata = {"performative": "query"}
        # template_learning_temperature.body = "temperature"
        # template_learning_temperature.sender = LEARNING_CONTACT

        await self.process_temperature()

        template_time_notif = Template()
        template_time_notif.metadata = {"performative": "notify"}
        template_time_notif.sender = "devices12@sure.im"

        template_query = Template()
        template_query.metadata = {"performative": "query"}

        template_fake = Template()
        template_fake.metadata = {"performative": "fake"}

        self.add_behaviour(self.RecvAndSendTemperatureBehav(), template_query)
        self.add_behaviour(self.ProcessTemperatureForNextTimeIndexBehav(), template_time_notif)
        self.add_behaviour(self.ParameterSelfCheckBehav(period=10))
        self.add_behaviour(self.DataCollectBehav(period=1))
        self.add_behaviour(self.DataCollectTimer(), template_fake)
        # self.add_behaviour(self.HeatingSelfCheckBehav())  # just once

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

    async def process_temperature(self):
        print("Temp. Model: Calculating next temperature...", end=" ")
        # self.set("temperature", float(msg.body))
        current_temp = float(self.get("current_temp"))
        temp_step = int(self.get("temp_step"))
        model = self.get("self")

        new_temperature_index = temperature_to_index(model.next_temperature(current_temp, temp_step))
        print(index_to_temperature(new_temperature_index))
        self.set("current_temp", index_to_temperature(new_temperature_index))
        async with sem2:
            with open("temperature_model.csv", "w") as f:
                f.write(f"{str(index_to_temperature(new_temperature_index))};")
        if self.get("state") != TemperatureAction.KEEP.value:
            temp_step += 1
            self.set("temp_step", temp_step)

    async def show_temps_and_heating(self):
        print("\n\nSaving Picture...\n\n")
        now = datetime.now()  # experimental
        # self.end_time = (now.hour * 3600 + now.minute * 60 + now.second) * INTERVAL_SHORTENER
        # non speed up, do I have to with index?
        self.end_time = time_index_to_seconds(int(self.get("last_time_index")))

        # data_heat = []
        # data_temp = []
        # start_time = None
        # TODO takhle asi udelat vsechny
        print(
            "start time",
            self.start_time,
            "(asi ",
            (self.start_time // (60 * 15)),
            ")",
            "end time",
            self.end_time,
            "(",
            (self.get("last_time_index")),
            ")",
        )
        req_zeros = np.full((self.end_time - self.start_time), np.nan)
        async with sem2:
            with open("requests.csv", "rt") as f:
                for request in f:
                    if request == "":
                        continue
                    arr = request.split(sep=";")
                    # print("time", arr[0], "increase/decrease", arr[1])
                    print(arr[0], end="-")
                    req_time = int(arr[0])
                    req_type = int(arr[1])
                    if req_time - self.start_time <= 0:
                        # bug
                        continue
                    req_zeros[self.end_time - req_time] = req_type
        await asyncio.sleep(0.5)
        # heating
        async with sem2:
            with open("requests.csv", "wt") as f:
                f.write("")
        print()

        fig, axs = plt.subplots(4, 1, layout="constrained")
        h = np.asarray(self.data_heat)
        yh = np.arange(self.start_time, self.start_time + h.size * 45, 45)
        axs[0].plot(yh, h)
        axs[0].set_title("Heating")

        smooth_temps = smoothen(np.asarray(self.data_temp))
        ysmoothen = np.arange(self.start_time, self.start_time + smooth_temps.size * 45, 45)
        print("smooth temps size:", smooth_temps.size, "last element:", smooth_temps[-1])
        axs[1].plot(ysmoothen, smooth_temps)
        axs[1].set_title("Temperatures")

        # yr = np.arange(self.start_time, self.start_time + req_zeros.size , 1)
        yr = np.arange(self.start_time, self.start_time + req_zeros.size, 1)
        r = np.asarray(req_zeros)
        axs[2].stem(yr, r, bottom=-1)
        axs[2].set_title("Requests")

        t = np.asarray(self.data_temp)
        print("temps size:", t.size, "last element:", t[-1])
        yt = np.arange(self.start_time, self.start_time + t.size * 45, 45)
        print(np.array_equal(yt, ysmoothen))
        axs[3].plot(yt, t)
        axs[3].set_title("Temperatures Non Smooth")

        # axs[1].plot(yt, t)

        # axs[1].set_xticks(np.arange(0, 100, 30), ['zero', '30', 'sixty', '90'])
        # axs[1].set_yticks([-1.5, 0, 1.5])  # note that we don't need to specify labels

        ax0_ticks = axs[0].get_xticks()
        ax1_ticks = axs[1].get_xticks()
        ax2_ticks = axs[2].get_xticks()
        ax3_ticks = axs[3].get_xticks()

        axs[0].set_xticklabels([str(timedelta(seconds=int(x))) for x in ax0_ticks])
        axs[1].set_xticklabels([str(timedelta(seconds=int(x))) for x in ax1_ticks])
        axs[2].set_xticklabels([str(timedelta(seconds=int(x))) for x in ax2_ticks])
        axs[3].set_xticklabels([str(timedelta(seconds=int(x))) for x in ax3_ticks])

        # axs[0].set_xticklabels([str(timedelta(seconds=int(x) * INTERVAL_SHORTENER)) for x in ax0_ticks])
        # axs[1].set_xticklabels([str(timedelta(seconds=int(x) * INTERVAL_SHORTENER)) for x in ax1_ticks])
        # axs[2].set_xticklabels([str(timedelta(seconds=int(x) // INTERVAL_SHORTENER)) for x in ax2_ticks])
        # axs[3].set_xticklabels([str(timedelta(seconds=int(x) * INTERVAL_SHORTENER)) for x in ax3_ticks])

        axs[2].set_yticks([-1, 0, 1])
        axs[2].set_yticklabels(["", "Increase", "Decrease"])

        axs[0].set_yticks([-1, 0, 1, 2])
        axs[0].set_yticklabels(["", "Heating", "Not heating", ""])
        plt.tight_layout()
        fig.savefig("fig")
        exit(0)
