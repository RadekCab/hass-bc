import asyncio
import numpy as np
from spade.agent import Agent as SpadeAgent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour, PeriodicBehaviour
from spade.template import Template
from spade.message import Message


from sim_user import SimUser
from sim_temperature import SimTemperature
from learning_sim import training, create_plan
from agent.agents import TIME_INTERVAL, sem

TEMPERATURE_DICT_PROPERTY = "init_inc_temp"
TEMPERATURE_DICT_INDEX = "init_inc_temp_index"
INIT_HEAT_TEMPERATURES = "heating_requests"
INIT_STOPHEAT_TEMPERATURES = "stopheat_requests"
LEARNING_SELF = "learning11@sure.im"
USER_GROUP_KNOWLEDGE = "test_user_1"


class LearningAgent(SpadeAgent):
    """
    - initalizes own temperature model with running few experimental requests
    - gets starting temperature and temperature after an hour of heating
    - and temperature after an hour of no heating
    - during time it should check changes from variety of
    starting temperatures

    - runs Q-learning sequence after new request received

    - (Not implemented) sends experimental requests and run Q-learning sequences depending on reactions

    Args:
        SpadeAgent class: Agent defined in Spade library
    """

    class RecvBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=6)  # wait for a message
            if msg:
                print("------Message received with content: {}".format(msg.body))

        async def on_end(self):
            await self.agent.stop()

    class RecvTimeplanBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=6)  # wait for a message
            if msg:
                # print(msg.body)
                if msg.body.split(sep=":", maxsplit=1)[0] == "timeplan_reply":
                    heat_dict, noheat_dict = self.get_timeplan_values_from_message(msg)

                    print(
                        "Learning Agent: Timeplan set. Default Temperature is:",
                        self.get("default_temperature"),
                    )
                    # print("heat:", heat_dict, "noheat", noheat_dict)
                    self.set("timeplan_heat", heat_dict)
                    self.set("timeplan_noheat", noheat_dict)
                else:
                    print("WARN Learning Agent: Wrong Timeplan Format Received")

        def get_timeplan_values_from_message(self, msg: Message):
            heat_noheat = msg.body.split(sep=":", maxsplit=1)[1]
            heat_dict = eval(heat_noheat.split(sep=";")[0])
            noheat_dict = eval(heat_noheat.split(sep=";")[1])
            return heat_dict, noheat_dict

    class RecvTemperatureBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)  # wait for a message
            if msg:
                mes_arr = msg.body.split(sep=":")
                if mes_arr[0] == "Temperature":
                    temp = mes_arr[1]
                    self.set("default_temperature", temp)
                elif mes_arr[0] == "Request":
                    Inhabitant = self.get(USER_GROUP_KNOWLEDGE)
                    heat_at = self.get("timeplan_heat")
                    noheat_at = self.get("timeplan_noheat")
                    time_interval = mes_arr[1].split(sep=";")[1]
                    if mes_arr[1] == "temperature_increase":
                        heat_at[time_interval] = "index"
                        self.set("timeplan_heat", heat_at)
                    elif mes_arr[1] == "temperature_decrease":
                        noheat_at[time_interval] = "index"
                        self.set("timeplan_noheat", noheat_at)
                    self.set("re_learn", True)
                else:
                    print("WARN Learning Agent: Received Unknown Message.")

    class RecvTemperatureInitBehav(CyclicBehaviour):
        async def run(self):
            if int(self.get(TEMPERATURE_DICT_INDEX)) != 0:
                print("INIT:", self.get(TEMPERATURE_DICT_INDEX), "/ 12")
            msg = await self.receive(timeout=5)  # wait for a message
            if msg:
                temp = msg.body.split(sep=":")[1]
                temp_dict = self.get(TEMPERATURE_DICT_PROPERTY)
                temp_dict[self.get(TEMPERATURE_DICT_INDEX) % 6] = temp
                self.set(TEMPERATURE_DICT_PROPERTY, temp_dict)
                i = self.get(TEMPERATURE_DICT_INDEX)
                self.set(TEMPERATURE_DICT_INDEX, i + 1)

    class TemperatureQueryBehav(PeriodicBehaviour):
        # add behaviour together with ParameterSelfCheckBehav !
        async def run(self):
            msg = Message(
                to="devices12@sure.im", sender=LEARNING_SELF, body="temperature"
            )  # Set the message content
            msg.set_metadata("performative", "query")
            await self.send(msg)
            print("Learning Agent: Message Request sent to TempAgent!")

    class DefaultTemperatureQueryBehav(OneShotBehaviour):
        # add behaviour together with ParameterSelfCheckBehav !
        async def run(self):
            await asyncio.sleep(3)
            msg = Message(
                to="devices12@sure.im", sender=LEARNING_SELF, body="temperature"
            )  # Set the message content
            msg.set_metadata("performative", "query")
            await self.send(msg)
            print("Learning Agent: Message Request sent to TempAgent!")

    class StartHeatingQueryBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(
                to="devices12@sure.im", sender=LEARNING_SELF, body="start_heating"
            )  # Set the message content
            msg.set_metadata("performative", "query")
            await self.send(msg)
            print("Learning Agent: Message Request sent to TempAgent!")

    class StopHeatingQueryBehav(OneShotBehaviour):
        async def run(self):
            msg = Message(
                to="devices12@sure.im", sender=LEARNING_SELF, body="stop_heating"
            )  # Set the message content
            msg.set_metadata("performative", "query")
            await self.send(msg)
            print("Learning Agent: Message Request sent to TempAgent!")

    class TimePlanQueryBehav(OneShotBehaviour):
        async def run(self):
            await asyncio.sleep(12)
            msg = Message(
                to="userinfo11@sure.im", sender=LEARNING_SELF, body="timeplan"
            )  # Set the message content
            msg.set_metadata("performative", "query")
            await self.send(msg)
            print("Learning Agent: Message Request sent to UserAgent!")

    class LearningBehav(OneShotBehaviour):
        async def run(self):
            Inhabitant = self.get(USER_GROUP_KNOWLEDGE)
            heat_at = list(self.get("timeplan_heat").keys())
            noheat_at = list(self.get("timeplan_noheat").keys())
            Inhabitant.process_temperature_targets_from_intervals(
                float(self.get("default_temperature")), heat_at, noheat_at
            )

            heat_temperatures = np.asarray(list(self.get("heating_requests").values()))
            stop_temperatures = np.asarray(list(self.get("stopheat_requests").values()))
            temperatures = np.vstack(
                (
                    heat_temperatures.astype(np.float16),
                    stop_temperatures.astype(np.float16),
                )
            )
            print("Learning Temperatures For Model:", temperatures)
            default_temp = float(self.get("default_temperature"))
            TemperatureModel = SimTemperature(default_temp, temperatures, exp_init=True)
            print(
                "Learning Starting Temperature In Env. Model:",
                TemperatureModel._starting_temperature,
            )

            print("Learning Agent: Started Learning. . .")
            print("Learning Agent: ", end=" ")
            q_table = training(default_temp, Inhabitant, TemperatureModel)
            print("Learning Agent: Strategy Saved To File Provided to Temp. Agent.")
            np.save("q_table", q_table)

    class ParameterSelfCheckBehav(PeriodicBehaviour):
        async def run(self):
            # for init
            activate_learning = True
            if int(self.get(TEMPERATURE_DICT_INDEX)) >= 12:
                b = self.get("period_temp_behav")
                if self.agent.has_behaviour(b):
                    print(
                        "Now we have gathered experimental data: ",
                        self.get(TEMPERATURE_DICT_PROPERTY),
                    )
                    self.agent.remove_behaviour(b)
                    self.set(TEMPERATURE_DICT_INDEX, 0)
                    self.set(
                        INIT_STOPHEAT_TEMPERATURES, self.get(TEMPERATURE_DICT_PROPERTY)
                    )
                    self.set("init_complete", True)
                print(
                    f"Initalization Temperatures (+): {self.get(INIT_HEAT_TEMPERATURES)}"
                )
                print(
                    f"Initalization Temperatures (-): {self.get(INIT_STOPHEAT_TEMPERATURES)}"
                )
            elif int(self.get(TEMPERATURE_DICT_INDEX)) == 6:
                print(
                    "Cleaning heat requests. Preparing to gather -stop heat- temperatures."
                )
                if self.get(TEMPERATURE_DICT_PROPERTY) != {}:
                    heat = self.get(TEMPERATURE_DICT_PROPERTY)
                    self.set(INIT_HEAT_TEMPERATURES, heat)
                self.set(TEMPERATURE_DICT_PROPERTY, {})
                stop_heat = self.get("stop_heating_behav")
                self.agent.add_behaviour(stop_heat)
            if (
                activate_learning
                and self.get("init_complete")
                and self.get("timeplan_heat") is not None
                and self.get("timeplan_noheat") is not None
            ):
                activate_learning = False
                learning_behav = self.get("learning_behav")
                self.agent.add_behaviour(learning_behav)
            if self.get("re_learn"):
                print("Learning Agent: Started re-learning User Model. . .")
                self.set("re_learn", False)
                activate_learning = False
                learning_behav = self.agent.LearningBehav()
                self.agent.add_behaviour(learning_behav)

        async def on_end(self):
            # stop agent from behaviour
            await self.agent.stop()

    async def setup(self):
        self.set(TEMPERATURE_DICT_INDEX, 0)
        self.set(TEMPERATURE_DICT_PROPERTY, {})
        self.set("default_temperature", None)

        # TODO presence
        Inhabitant = SimUser(USER_GROUP_KNOWLEDGE, leave=[10], arrive=[13])
        self.set(USER_GROUP_KNOWLEDGE, Inhabitant)
        print("Learning agent started.")

        template1 = Template()
        template1.sender = "device12@sure.im"
        template1.metadata = {"performative": "inform"}

        template2 = Template()
        template2.set_metadata("performative", "inform")
        template2.sender = "devices12@sure.im"

        template3 = Template()
        template3.set_metadata("performative", "inform")
        template3.sender = "userinfo11@sure.im"

        template4 = Template()
        template4.set_metadata("performative", "notify")
        template4.sender = "devices12@sure.im"

        if self.get("init"):
            print("Learning agent: Initializing experiments")
            increase_behav = self.StartHeatingQueryBehav()
            recv_temp_behav = self.RecvTemperatureInitBehav()
            stop_heat_behav = self.StopHeatingQueryBehav()
            self.set("stop_heating_behav", stop_heat_behav)
            ask_temperature_after_period_behav = self.TemperatureQueryBehav(
                period=TIME_INTERVAL
            )
            self.set("period_temp_behav", ask_temperature_after_period_behav)
            self.add_behaviour(ask_temperature_after_period_behav)
            self.add_behaviour(increase_behav)
            self.add_behaviour(recv_temp_behav, template2)

        if self.get("learning"):
            print("Learning agent: Initializing learning")
            send_timeplan_request_behav = self.TimePlanQueryBehav()
            recv_timeplan_behav = self.RecvTimeplanBehav()
            send_default_temp_query_behav = self.DefaultTemperatureQueryBehav()
            recv_default_temp_behav = self.RecvTemperatureBehav()
            recv_temp_request_behav = self.RecvTemperatureBehav()
            learning_behav = self.LearningBehav()
            self.set("learning_behav", learning_behav)
            self.add_behaviour(send_default_temp_query_behav)
            self.add_behaviour(recv_default_temp_behav, template2)
            self.add_behaviour(send_timeplan_request_behav)
            self.add_behaviour(recv_timeplan_behav, template3)
            self.add_behaviour(recv_temp_request_behav, template4)

        self.add_behaviour(self.ParameterSelfCheckBehav(period=6))

    def initalize_temperature_model():
        pass
