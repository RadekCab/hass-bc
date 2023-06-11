import numpy as np
from faker import Faker
from faker.providers import DynamicProvider
from datetime import timedelta
import random
import uuid


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
    user_cold_generator = UserColdGenerator()
    time_requests = []
    for _ in range(req_cnt):
        _, temp = user_cold_generator.generate_temperature_request(mins)
        time_requests.append(temp)
    print(time_requests)
    # _ , time_request = user_cold_generator.generate_temperature_request()

    cold_requests_timestamps = [time_intervals[x] for x in time_requests]
    print(cold_requests_timestamps)
    return time_requests


def get_exp_temp_values(time_requests, interval):
    mins = int(1440 / interval)
    curr_temp_arr = np.full(mins, nearest_pointfive(random.uniform(15, 25)))
    print(curr_temp_arr)

    pass


def nearest_pointfive(num):
    return round(num * 2) / 2


if __name__ == "__main__":
    # TODO simulation, random events for users
    # values for one day after random increase requests
    temperatures_day = get_exp_temp_values(generate_cold_requests(15), 15)

    pass
