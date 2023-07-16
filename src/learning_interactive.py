
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
# Get plan from HASS
from sim import gather_heat_requests
# fake error here IPython has async covered
heat_requests = await gather_heat_requests()
print("heat at:", heat_requests[0])
print("stop heat at:", heat_requests[1])

#%%
#Format and retrieve time interval
#TODO loop and process more
from datetime import datetime
heat_at = datetime.strptime(heat_requests[0][0], '%Y-%m-%d %H:%M:%S')
noheat_at = datetime.strptime(heat_requests[1][0], '%Y-%m-%d %H:%M:%S')
heat_minutes = heat_at.minute + heat_at.hour*60
noheat_minutes = noheat_at.minute + noheat_at.hour*60
heat_index = int(round(heat_minutes/15))
noheat_index = int(round(noheat_minutes/15))
Inhabitant = SimUser("1", leave=[16],arrive=[26], targets={0: 18, 26: 23})


# %%
# Start the simulation learning of the next day
# SimUset sends feedback at the same times again
# if he doesnt have desired temperature there

# Some training notes:
#
from learning_sim import training, create_plan
from events import nearest_pointfive, exp_increase_array_at_indeces, generate_cold_requests
from sim_user import SimUser
from sim_temperature import SimTemperature
import random
Inhabitant = SimUser("1", [16],[26], {0: 18, 26: 23})

starting_temp = nearest_pointfive(random.uniform(18, 19.6))
#starting_temp = 23.5
TemperatureEnvironment = SimTemperature(starting_temp)
result_q_table = training(starting_temp, Inhabitant, TemperatureEnvironment)
print(result_q_table)
# %%
# Now lets see ideal actions for day 2
optimal_temp_actions = create_plan(starting_temp,result_q_table,Inhabitant,
                                   TemperatureEnvironment,mode="model_only")

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

# TODO
# next up... 
# - [x] zásahy do optimal (přes hass a agenty), spustí/vypnou topení na určitou dobu,
#   [] výstup => spuštěný learning do dalšího dne
# - [] snažší úprava presence intervalů -> [] vyřešit hass plánem
# - momentálně má k dispozici jasnej model uživatelových cílů. TODO vytvopřit hass plán
#   a z něj model vydedukovat
# 
# 

