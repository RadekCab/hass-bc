
from events import nearest_pointfive
from myenum.action import TemperatureAction
import random


UPPER_LIMIT = 25
BOTTOM_LIMIT = 15
DELTA_LIMIT = 5

#TODO eliminate starting and stopping heating rapidly, probably using numbers here
class SimTemperature():
    def __init__(self, starting_temperature):
        self._starting_temperature = starting_temperature
        # eliminate starting and stopping heating rapidly
        self._speed_up_factor = random.uniform(1.008,1.02)
        self._EXP_CONSTANTS =  [x*self._speed_up_factor for x in [1.030, 1.036,
                               1.055, 1.082,
                               1.121, 1.177]]
        
        
        
    def next_temperature(self, current_temperature, step, is_decrease=False):
        next_temperature = None
        if is_decrease:
            next_temperature = nearest_pointfive(
                                 current_temperature*
                                 (1/self._EXP_CONSTANTS[step]))
        else:
            next_temperature = nearest_pointfive(
                                 current_temperature*
                                 (self._EXP_CONSTANTS[step]))
        # pointless reality simulation which doesnt work well
        #if abs(next_temperature-self._starting_temperature) > DELTA_LIMIT:
            #return current_temperature
        if BOTTOM_LIMIT <= next_temperature <= UPPER_LIMIT:
            return next_temperature
        if next_temperature > UPPER_LIMIT:
            #print("OVF, returing upper limit")
            return UPPER_LIMIT
        if next_temperature < BOTTOM_LIMIT:
            #print("OVF, returing bottom limit")
            return BOTTOM_LIMIT
        
    class FastSwitchException(Exception):
        pass
        
        