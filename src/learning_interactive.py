
#%%
from events import nearest_pointfive, exp_increase_array_at_indeces, generate_cold_requests
from utils import find_nearest
from sim_user import SimUser
from sim_temperature import SimTemperature
from learning_sim import training, create_plan
import numpy as np
import random
import matplotlib.pyplot as plt
from datetime import timedelta

def plot_it(arr : np.ndarray):
    fig, axs = plt.subplots(1, 1)
    d = np.arange(0, 96, 1)
    axs.plot(d, arr)
    plt.xlim([0,95])
    plt.xticks(np.arange(0, 96, 19))
    current_values = axs.get_xticks()
    print(current_values)
    
    axs.set_xticklabels([str(timedelta(minutes=int(x) * 15)) for x in current_values])
    
    axs.grid(True)
    # axs[0].set_xlim(str(timedelta(minutes=0)), str(timedelta(minutes=1440)))
    plt.show()
    
def to_insert_reflex_agent_inputs():
    starting_temp = nearest_pointfive(random.uniform(18, 19.6))
    temperature_day = np.full(DAY_INTERVALS,starting_temp)
    Inhabitant = SimUser()
    #req_gen = Inhabitant.get_requests_by_target_temp(temperature_day)
    temperature_day_after_fdb = np.full(DAY_INTERVALS,starting_temp)
    # for (time_index,request) in req_gen:
    #     temperature_day_after_fdb = exp_increase_array_at_indeces(temperature_day,{time_index: request})
    #     req_gen.send(temperature_day_after_fdb)
    for i in range(Inhabitant.get_request_count()):
        time_index, request = Inhabitant.get_requests_by_target_temp(
            temperature_day, i)
        # TODO this should behave same as temperature
        # TODO not using user presence?
        temperature_day = exp_increase_array_at_indeces(temperature_day,{time_index: request})
    plot_it(temperature_day)


#%%
# Create 1 day data + Feedback by dummy inhabitant.
# That will represent reflex agent behavior while
# changing thermostat value manually.
DAY_INTERVALS = 96
#to_insert_reflex_agent_inputs()



#%%
# Set default Room1 temperature so user sees it in HASS UI
DEFAULT_TEMPERATURE = 20
from sim import set_default_temperature
set_default_temperature(DEFAULT_TEMPERATURE)

#%%
#Get plan from HASS
from sim import gather_heat_requests
# fake error here IPython has async covered
heat_requests = await gather_heat_requests()
print("heat at:", heat_requests[0])
print("stop heat at:", heat_requests[1])

#%%
# Format and retrieve time intervals
#TODO loop and process more
from datetime import datetime
heat_at = datetime.strptime(heat_requests[0][0], '%Y-%m-%d %H:%M:%S')
noheat_at = datetime.strptime(heat_requests[1][0], '%Y-%m-%d %H:%M:%S')
heat_minutes = heat_at.minute + heat_at.hour*60
noheat_minutes = noheat_at.minute + noheat_at.hour*60
heat_index = int(round(heat_minutes/15))
noheat_index = int(round(noheat_minutes/15))

#%%
# Extract targets solely by Time Plan
# E.G.( Default: 20, Heat[12,52], Stop_Heat[24,72] =>
# (0-12)=20, (12-24)=>20, (24-52)=<20, (52-72)=>20., (72-96)=<20) )
heat_times = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in heat_requests[0]]
noheat_times = [datetime.strptime(x, '%Y-%m-%d %H:%M:%S') for x in heat_requests[1]]
heat_indices = [int(round((x.minute + x.hour*60)/15)) for x in heat_times]
noheat_indices = [int(round((x.minute + x.hour*60)/15)) for x in noheat_times]
print(heat_indices, noheat_indices)
#%%
from sim_user import SimUser
DEFAULT_TEMPERATURE = 20
heat_indices = [32,84]
noheat_indices = [60]

Inhabitant = SimUser("1", leave=[16], arrive=[26])
Inhabitant.process_temperature_targets_from_intervals(DEFAULT_TEMPERATURE, 
                                                      heat_indices, noheat_indices)
print("Inhabitant created")
print(Inhabitant.target_temp_time)

# %%
# Start the simulation learning of the next day
# SimUset sends feedback at the same times again
# if he doesnt have desired temperature there

# Some training notes:
#
import numpy as np
from learning_sim import training, create_plan
from events import nearest_pointfive, exp_increase_array_at_indeces, generate_cold_requests
from sim_user import SimUser
from sim_temperature import SimTemperature
import random
#Inhabitant = SimUser("1", [16],[26], {0: 18, 26: 23})

#starting_temp = nearest_pointfive(random.uniform(18, 19.6))
#starting_temp = 23.5
#TemperatureEnvironment = SimTemperature(DEFAULT_TEMPERATURE)

# simulate 6 and 6 intervals of resulted temperature experimenting
DEFAULT_TEMPERATURE = 20
heat_temperatures = [20,20.5,20.5,21.5555555,21.5,22]
stop_temperatures = [20,20,19.5,19.5,19,19]
after_actions = heat_temperatures
after_actions = np.vstack((after_actions, stop_temperatures))

TemperatureEnvironment = SimTemperature(DEFAULT_TEMPERATURE, after_actions,exp_init=True)
result_q_table = training(DEFAULT_TEMPERATURE, Inhabitant, TemperatureEnvironment)
#print(result_q_table)
# %%
import numpy as np
import matplotlib.pyplot as plt
from datetime import timedelta

def plot_it(arr : np.ndarray):
    fig, axs = plt.subplots(1, 1)
    d = np.arange(0, 96, 1)
    axs.plot(d, arr)
    plt.xlim([0,95])
    plt.xticks(np.arange(0, 96, 19))
    current_values = axs.get_xticks()
    print(current_values)
    
    axs.set_xticklabels([str(timedelta(minutes=int(x) * 15)) for x in current_values])
    
    axs.grid(True)
    # axs[0].set_xlim(str(timedelta(minutes=0)), str(timedelta(minutes=1440)))
    plt.show()




# Now lets see ideal actions for day 2
optimal_temp_actions = create_plan(DEFAULT_TEMPERATURE,result_q_table,Inhabitant,
                                   TemperatureEnvironment,mode="")

plot_it(optimal_temp_actions)
# 0-16,26-66: 21 ; 66 - 96: 20
targets = list(Inhabitant.target_temp_time.values())
target_times = list(Inhabitant.target_temp_time.keys())
print(f"User wants {str(timedelta(minutes=int(0) * 15))}-{str(timedelta(minutes=int(Inhabitant.leave[0]) * 15))}"+
      f", {str(timedelta(minutes=int(Inhabitant.arrive[0]) * 15))}-{str(timedelta(minutes=int(target_times[1]) * 15))}:"+
      f" {targets[0]} ; {str(timedelta(minutes=int(target_times[1]) * 15))} -" + 
      f" {str(timedelta(minutes=int(96) * 15))}: {targets[1]}")

# Lets visualize these actions
# TODO zvetsujem po pulstupnich, takze si s tim jeste pohraj
# a pro startovni temperature vykresli vysledek simulace
# for time_action in optimal_temp_actions:
#     if time_action[1] != -1:
#         if time_action[1] == 0:
#             print("Increase at", time_action[0])
#         if time_action[1] == 1:
#             print("Decrease at", time_action[0])


# %%
