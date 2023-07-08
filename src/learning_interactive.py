
#%%
from events import nearest_pointfive, exp_increase_array_at_indeces, generate_cold_requests
from utils import find_nearest
from sim_user import SimUser
from learning_sim import training
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


DAY_INTERVALS = 96
#%%
# Create 1 day data + Feedback by dummy inhabitant.
# That will represent reflex agent behavior while
# changing thermostat value manually.

starting_temp = nearest_pointfive(random.uniform(15, 20))
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
    temperature_day = exp_increase_array_at_indeces(temperature_day,{time_index: request})



print(np.unique(temperature_day))
print(temperature_day)
# %%
# I can plot it
plot_it(temperature_day)

# %%
# Start the simulation learning of the next day
# SimUset sends feedback at the same times again
# if he doesnt have desired temperature there

training(temperature_day, Inhabitant)
