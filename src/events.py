import numpy as np
from faker import Faker
from faker.providers import DynamicProvider
from datetime import timedelta
import random
import uuid

# import matplotlib.pyplot as plt


class Generator:
    def __init__(self) -> None:
        self.fake = Faker()

    def get_faker(self):
        return self.fake


class UserPresenceGenerator(Generator):
    def __init__(self) -> None:
        super().__init__()
        self.home_members_provider = DynamicProvider(
            provider_name="user_id",
            elements=[uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4()],
        )


class UserColdGenerator(Generator):
    def generate_temperature_request(self, mins):
        home_members_provider = DynamicProvider(
            provider_name="user_id", elements=["001", "002", "003", "004"]
        )

        fake = self.get_faker()
        fake.add_provider(home_members_provider)
        # print(fake.user_id())
        # users = [fake.unique.user_id() for i in range(4)]
        # print(users)
        # faker.seed(555) # for unit testing
        time_index = int(round(random.uniform(0, mins), 1))

        user_req = fake.user_id(), time_index
        return user_req


def generate_cold_requests(interval=15) -> list:
    mins = int(1440 / interval)
    intervals = np.linspace(0, 1440, mins)
    time_intervals = [str(timedelta(minutes=x)) for x in intervals]
    # req_cnt = int(random.uniform(1, 4))

    req_cnt = 1
    # User Specific
    # user_cold_generator = UserColdGenerator()
    time_requests = []
    # for _ in range(req_cnt):
    #     _, temp = user_cold_generator.generate_temperature_request(mins)
    #     time_requests.append(temp)

    time_requests = get_user_feedback()

    # debug formatted
    # cold_requests_timestamps = [time_intervals[x] for x in time_requests]
    # print(cold_requests_timestamps)
    return time_requests


def get_user_feedback(scenario="scenario1"):
    index_wakeup_increase = -1
    index_backfromwork_increase = -1
    index_reading_decrease = -1
    index_sleep_increase = -1
    indeces = {}
    if scenario == "scenario1":
        indeces = {25: "increase", 
                   65: "decrease"}
    elif scenario == "scenario2":
        indeces = {25: "increase"}

    time_requests = offset_feedback_time(indeces)
    print("time requests:", time_requests)
    # time_requests.append(random_action_time_offset(index_wakeup_increase))
    # time_requests.append(random_action_time_offset(index_backfromwork_increase))
    # time_requests.append(random_action_time_offset(index_reading_decrease))
    # time_requests.append(random_action_time_offset(index_sleep_increase))
    return time_requests

def offset_feedback_time(indeces):
    return {random_action_time_offset(x):a for (x,a) in indeces.items()}


def random_action_time_offset(index: int):
    return index + int(round(random.uniform(-4, 4)))


def get_exp_temp_values(time_requests, interval, start_temp):
    mins = int(1440 / interval)
    curr_temp_arr = np.full(mins, start_temp)
    # print(curr_temp_arr)
    heated_arr = exp_increase_array_at_indeces(curr_temp_arr, time_requests)
    # print(heated_arr)
    return heated_arr


def exp_increase_array_at_indeces(arr, feedback_indeces : dict, type="temperature"):
    # warning, indeces additionally overlap each other
    if type == "temperature":
        # 6 indeces after action trigger, we get desired temperature
        # that stays to the end of the list (day)
        # TODO refactor
        for (index,action) in feedback_indeces.items():
            sliced_arr = arr[index : index + 6]  # x, x+1, x+2, x+3, x+4, x+5
            log_modif = []
            if sliced_arr[0] >= 30:
                log_modif = sliced_arr
            else:
                if action == "increase":
                    # TODO it overflows above 25
                    log_modif = np.logspace(1, 1.04, num=6, base=sliced_arr[0])
                else:
                    # print("dec")
                    log_modif = np.logspace(1, 0.96, num=6, base=sliced_arr[0])
            # print("change = index:", index, "exp:", log_modif)
            arr = np.concatenate(
                [
                    arr[:index],
                    log_modif,
                    np.full((arr[index + 6 :]).size, log_modif[-1]),
                ]
            )
        return nearest_pointfive(arr)


def nearest_pointfive(num):
    if type(num) is np.ndarray:
        return np.around(num * 2) / 2
    return round(num * 2) / 2


if __name__ == "__main__":
    # TODO simulation, random events for users
    # values for one day after random increase requests
    pass
