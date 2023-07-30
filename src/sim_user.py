
import numpy as np
from myenum.action import TemperatureAction
from utils import index_to_temperature, temperature_to_index

class SimUser():
    def __init__(self,name,leave : list, arrive : list, targets: dict ={}, is_sim=True):
        self._setting = 1
        # sorted!
        self.target_temp_time = targets
        # leave, arrive
        self.leave = leave # [16]
        self.arrive = arrive # [26]
        # time when they scream when wrong tempearture is there
        self._present_time = self._calc_present_time(leave, arrive)
        self._name = name
        # false for real time request gathering (viz get_latest_request_time)
        self.is_sim = is_sim

    def _calc_present_time(self,leave, arrive):
        # TODO will change with hass timeplan
        return np.hstack((np.arange(0,leave[0],1),np.arange(arrive[0],96,1)))

    def get_present_time(self):
        return self._present_time

    def get_name(self):
        return self._name
    
    def set_name(self, name):
        self._name = name
        
    def get_request_count(self):
        return len(self.target_temp_time)

    def get_setting(self):
        return self._setting

    def set_setting(self, value):
        self._setting = value

    def get_requests_by_target_temp(self, temp_day, request_index) -> dict:
        tg_time_index = list(self.target_temp_time.keys())[request_index]
        tg_temperature = self.target_temp_time[tg_time_index]
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
    def get_user_request_per_timeframe(self, time_index, temperature_index, tolerance=0.5):
        # inhabitants always send requests when they're angry
        # +- values are to prevent hyperactive user
        if self._setting == 1:
            if time_index in self.target_temp_time:
                if index_to_temperature(temperature_index) > self.target_temp_time[time_index]+0.5:
                    # decrease
                    return TemperatureAction.DECREASE
                if index_to_temperature(temperature_index) < self.target_temp_time[time_index]-0.5:
                    return TemperatureAction.INCREASE
                else: 
                    return None
            elif time_index in self._present_time:
                # find the first feedback/request before this time index
                latest_request_time = self._get_latest_request_time(time_index, self.is_sim)
                if latest_request_time is not None:  
                    latest_target_temperature = self.target_temp_time[latest_request_time]
                    if index_to_temperature(temperature_index) > latest_target_temperature+tolerance:
                        return TemperatureAction.DECREASE
                    if index_to_temperature(temperature_index) < latest_target_temperature-tolerance:
                        return TemperatureAction.INCREASE
                    else:
                        return None
                else:
                    return None
            else:
                return None

    # if sim is True, first target temperature is taken from the nearest future
    # cant be used in real time (use sim=False), but will work with time plan
    def _get_latest_request_time(self, time_index, sim=True):
        tg_time = list(self.target_temp_time.keys())
        time_index_present = np.searchsorted(self._present_time, time_index, side='left')
        relevant_time_indeces = self._present_time[:time_index_present+1]
        relevant_requests = []
        sim_no_requests_yet = False
        # runs twice at max
        while len(relevant_requests) == 0: 
            for fb in tg_time:
                present_feedback = np.argwhere(relevant_time_indeces==fb)
                if present_feedback.size > 0:
                    relevant_requests.append(np.argwhere(relevant_time_indeces==fb))
            if len(relevant_requests) == 0 and sim:
                relevant_time_indeces = self._present_time       
                sim_no_requests_yet = True
            elif len(relevant_requests) == 0:
                print(f"User {self._name}: no request in present time.")
                return None
        relevant_requests = np.asarray(relevant_requests)
        if sim_no_requests_yet:
            return relevant_time_indeces[np.min(relevant_requests)]
        return relevant_time_indeces[np.max(relevant_requests)]
    
    def process_temperature_targets_from_intervals(self,baseline,heat_at,noheat_at):
        for h in heat_at:
            if h == -1:
                continue
            self.target_temp_time[h] = baseline+1
        for h in noheat_at:
            if h == -1:
                continue
            self.target_temp_time[h] = baseline-1
  
    setting = property(get_setting, set_setting, doc="Current setting.")
    name = property(get_name, set_name, doc="Name.")
    
    