import random
import numpy as np

from events import nearest_pointfive
from myenum.action import TemperatureAction


UPPER_LIMIT = 25
BOTTOM_LIMIT = 15
DELTA_LIMIT = 5


class SimTemperature:
    """Class used for building temperature model of learning agent"""

    # exp_init if we are learning from (semi)real environment
    def __init__(
        self, starting_temperature, exp_temperature_after_actions=None, exp_init=False
    ):
        self._starting_temperature = starting_temperature
        # eliminate starting and stopping heating rapidly
        self._speed_up_factor = random.uniform(1.008, 1.02)
        if not exp_init:
            self._EXP_HEAT_CONSTANTS = [
                x * self._speed_up_factor
                for x in [1.030, 1.036, 1.055, 1.082, 1.121, 1.177]
            ]

            self._EXP_STOP_CONSTANTS = [
                x * self._speed_up_factor
                for x in [1.030, 1.036, 1.055, 1.082, 1.121, 1.177]
            ]
        else:
            self._EXP_HEAT_CONSTANTS = np.zeros(6)
            self._EXP_STOP_CONSTANTS = np.zeros(6)
            self._calc_constants_from_temperatures(
                starting_temperature, exp_temperature_after_actions
            )

    # 2d array of 2x6 elements containg temperatures in 6 intervals after starting and stopping heating
    def _calc_constants_from_temperatures(
        self, starting_temp, exp_temperature_after_actions: np.ndarray, intervals=6
    ):
        exp_heat_temps = exp_temperature_after_actions[0]
        exp_stop_temps = exp_temperature_after_actions[1]
        for i in range(intervals):
            self._EXP_HEAT_CONSTANTS[i] = (1 - starting_temp / exp_heat_temps[i]) + 1
            self._EXP_STOP_CONSTANTS[i] = starting_temp / exp_stop_temps[i]

    def next_temperature(self, current_temperature, step, is_decrease=False):
        next_temperature = None
        if is_decrease:
            next_temperature = nearest_pointfive(
                current_temperature * (1 / self._EXP_STOP_CONSTANTS[step])
            )
        else:
            next_temperature = nearest_pointfive(
                current_temperature * (self._EXP_HEAT_CONSTANTS[step])
            )
        if BOTTOM_LIMIT <= next_temperature <= UPPER_LIMIT:
            return next_temperature
        if next_temperature > UPPER_LIMIT:
            return UPPER_LIMIT
        if next_temperature < BOTTOM_LIMIT:
            return BOTTOM_LIMIT

    class FastSwitchException(Exception):
        pass
