
import numpy as np

class SimUser():
    def __init__(self):
        self._setting = 1
        # sorted!
        self._target_temp_time = {28: 21, 66: 20}

    def get_request_count(self):
        return len(self._target_temp_time)

    def get_setting(self):
        return self._setting

    def set_setting(self, value):
        self._setting = value

    def del_setting(self):
        del self._setting

    def get_requests_by_target_temp(self, temp_day, request_index) -> dict:
        tg_time_index = list(self._target_temp_time.keys())[request_index]
        tg_temperature = self._target_temp_time[tg_time_index]
        if temp_day[int(tg_time_index)] < tg_temperature:
            return (tg_time_index, "increase")
        elif temp_day[int(tg_time_index)] > tg_temperature:
            return (tg_time_index, "decrease")
        else:
            print("No feedback, temperature OK.+")
            return None
        
    # potom co processnu vystup learningu
    # odsimuluje se nova teplota s novym setpointem
    # cas a nove teploty vstupem funkce
    def process_feedback(self, time_temps : dict):
        if self._setting == 1:
            if time_temps[28] == 20:
                return 1
            if time_temps[66] == 19:
                return -1
            
    # for training
    def get_user_request_per_timeframe(self, time_index, temperature_index):
        # inhabitants always send requests when they're angry
        if self._setting == 1:
            if time_index in self._target_temp_time:
                if temperature_index > self._target_temp_time[time_index]:
                    # decrease
                    return 1
  
    setting = property(get_setting, set_setting, del_setting, "Current setting.")
    
    