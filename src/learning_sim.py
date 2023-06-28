# %%
from events import nearest_pointfive, get_exp_temp_values, generate_cold_requests
from utils import find_nearest
import numpy as np
import random
import matplotlib.pyplot as plt
from datetime import timedelta
from statistics import mean
from pprint import pprint

actions = ["increase", "decrease"]


def get_rewards(temperature_days: np.array, feedback_days):
    return calc_reward_for_states(temperature_days, feedback_days)
    # q_arr = m = np.zeros((96, 2))
    # TODO


def calc_reward_for_states(temperature_days, feedback_days) -> np.array:
    # calculation using custom reward function conditions and formulas
    rewards = np.zeros((96, 20))
    temps_const = np.arange(15, 25, 0.5)
    beta = 10
    alpha = 0.2
    sigma = 0.2
    ZARAZKA = False
    for days_sum,temperature_day in enumerate(temperature_days):
        for delta_index, state in enumerate(temperature_day):
            for i, t in enumerate(temps_const):
                # S: 24/06/2023
                s = rewards_simple(state, delta_index, feedback_days, t)
                if days_sum > 0:
                    rewards[delta_index, i] = round(mean([rewards[delta_index, i], s]),0)
                #s *= sigma
                else:
                    rewards[delta_index, i] = s

                if ZARAZKA:
                    # B:
                    b = rewards_getb(state, delta_index, feedback_days, t)
                    b *= beta
                    rewards[delta_index, i] = b

                # A:
                # a = rewards_geta(delta_index, feedback_days)
    print(np.unique(rewards))
    return rewards


def rewards_geta(delta_index, feedback_days) -> float:
    # seems pointless now
    pass


"""_summary_
_params_
state: temperature 
delta_index: time_interval of state as integer
feedback_days: all feedback indeces (and action) received in each day
temperature_days: all temperatures
"""


def rewards_simple(state, delta_index, feedback_days, temperature_table) -> int:
    state_reward = 0
    # increase feedback: 18/25, 20/48, 22/63
    # jsme napr na 18/24
    # TODO MULTIPLE FEEDBACKS closest last, closes next for 1 person
    # TODO add more complexity with more feedbacks with different weigths
    fdb_array = [key for key in feedback_days]
    # todo all days
    #print(fdb_array[0])
    keys = fdb_array[0].keys()
    keys_list = [x for x in keys]
    #print(keys_list)
    relevant_fdb = find_nearest(keys_list,delta_index)
    #print(relevant_fdb)
    relevant_fdb_action = feedback_days[0][relevant_fdb]
    #for i, feedback in enumerate(np.array(feedback_days).flatten()):
    # get time delta 
    delta = delta_index - relevant_fdb
    state_reward = calc_simple_reward(delta,state,temperature_table,relevant_fdb_action)
    return state_reward

# TODO Tyhle odmeny zatim zvysuji teplotu jen pred feedbackem a to az moc dlouho, ale pak nezustane
def calc_simple_reward(delta,state,temperature_table,action):
    # td: 20 - (19+2)  = -1 => o 1 mensi teplota nez ma byt
    # !!! +2 pro inrease (v danem stavu chci priste o 2 stupne vic) !!!
    temperature_delta = temperature_table - (state + 2)
    # TODO decrease rewards
    # delta: 17 - 15 = 2 => >2feedback byl pred vic nez dvema intervaly
    reward = 0
    if delta >= 1:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = -36
            if temperature_delta <=-2: reward = -36
        else:
            pass
    # feedback bude az za vic nez dva intervaly
    if delta < -2:
        if action=="increase":
            if temperature_delta >=2: reward = -36
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 0
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -36
        else:
            pass
    if delta == -2:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = 12
            if temperature_delta <=-2: reward = 0
        else:
            pass
    if delta == -1:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = 36
        else:
            pass
    if delta == 0:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 36
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -36
        else:
            pass
    return reward


def rewards_getb(state, delta_index, feedback_days, temperature_table) -> int:
    # TODO feedback should be with action
    # TODO currently 2nd feedback is decrease (too hot in room)
    importance = 0
    for i, feedback in enumerate(np.array(feedback_days).flatten()):
        time_importance = False
        value_importance = False
        value_contradiction = False
        # feedback received in later time interval then current
        # TODO feedback.increase
        if feedback > delta_index:
            delta = feedback - delta_index
            if delta >= 2 and delta <= 4:
                time_importance = True
        # feedback is decrease temperature
        # TODO PREDELEJ TEN FEEDBACK!!!
        day = 0
        for j in range(i):
            if j % 4 == 0:
                day += 1
        # feedback_temp = temperature_days[day][feedback]

        if i % 2 == 0 and i % 4 != 0:
            if temperature_table < state:
                value_importance = True
            else:
                value_contradiction = True
        else:
            if temperature_table > state:
                value_importance = True
            else:
                value_contradiction = True
        if time_importance and value_importance:
            importance += 1
        # if value_contradiction:
        #    importance -= 1
    if importance >= 1:
        return 1
    if importance <= 1:
        return -1
    else:
        return 0


def get_starting_state():
    #curr_time_index = np.random.randint(95)
    #curr_temperature_index = np.random.randint(19)
    #return curr_time_index, curr_temperature_index
    # TODO real temperature
    return 0,9


def is_positively_rewarded(time_index, temperature_index, rewards):
    # TODO now just -10
    if rewards[time_index, temperature_index] <= 0:
        return False
    else:
        return True


def get_next_action(time_index, temperature_index, epsilon, q_values):
    if np.random.random() < epsilon:
        return np.argmax(q_values[time_index, temperature_index])
    else:
        return np.random.randint(2)


def perform_action(current_time_index, current_temperature_index, action: int):
    # TODO INTRODUCE KEEP TEMPERATURE ACTION
    new_time_index = current_time_index
    new_temperature_index = current_temperature_index
    if action == 0 and current_temperature_index != 19:
        new_temperature_index += 1
    if action == 1 and current_temperature_index != 0:
        new_temperature_index -= 1
    return new_time_index, new_temperature_index


def training(rewards: np.array):
    q_table = np.zeros((96, 20, 2))
    epsilon = 0.95
    discount_factor = 0.9
    learning_rate = 0.95
    # I don't think time index is changing at all in learning
    for episode in range(1000):
        # starting time and temperature
        time_index, temperature_index = get_starting_state()
        # choose between positively rewarded states
        starting_time = time_index
        while not is_positively_rewarded(time_index, temperature_index, rewards):
            # choose action
            action = get_next_action(time_index, temperature_index, epsilon, q_table)
            old_temperature_index = temperature_index
            time_index, temperature_index = perform_action(
                time_index, temperature_index, action
            )
            # TODO Rewarding action ?
            reward = rewards[time_index, temperature_index]
            # calculate temporal difference
            old_q_value = q_table[time_index, old_temperature_index, action]
            temporal_difference = reward + (
                discount_factor * np.max(q_table[time_index, temperature_index])
            )
            # update q for previous state acton pair
            new_q_value = old_q_value + (learning_rate * temporal_difference)
            q_table[time_index, old_temperature_index, action] = new_q_value

            # move to next time interval
            if time_index != 95:
                time_index += 1
                # 24h reached
                if time_index == starting_time:
                    break
            else:
                time_index = 0
    #print(np.unique(q_table))
    print("Traning Complete!")


def get_plan(rewards: np.array):
    pos = np.argwhere(rewards >= 0)
    print(pos)
    for i, j in pos:
        print(i, j)


if __name__ == "__main__":
    temperature_days = np.zeros((3, 96))
    starting_temp = nearest_pointfive(random.uniform(15, 20))
    feedback_days = []
    scenario = 1
    for i in range(3):
        # TODO tune feedback to have decrease requests
        feedback = generate_cold_requests(15)
        feedback_days.append(feedback)
        temperatures_day = get_exp_temp_values(feedback, 15, starting_temp)
        print("DAY", i, ":")
        print(temperatures_day)
        temperature_days[i] = temperatures_day
        starting_temp = temperatures_day[0]
    print("FEEDBACKS:", feedback_days)
    fig, axs = plt.subplots(3, 1)
    d = np.arange(0, 96, 1)
    axs[0].plot(d, temperature_days[0])
    axs[1].plot(d, temperature_days[1])
    axs[2].plot(d, temperature_days[2])
    current_values = axs[0].get_xticks()
    axs[0].set_xticklabels([str(timedelta(minutes=x * 15)) for x in current_values])
    axs[1].set_xticklabels([str(timedelta(minutes=x * 15)) for x in current_values])
    axs[2].set_xticklabels([str(timedelta(minutes=x * 15)) for x in current_values])
    axs[0].grid(True)
    axs[1].grid(True)
    axs[2].grid(True)
    # axs[0].set_xlim(str(timedelta(minutes=0)), str(timedelta(minutes=1440)))
    plt.show()
    # %%
    rewards = get_rewards(temperature_days, feedback_days)
    
    print(rewards)
    #%%
    training(rewards)
    # %%
    # get_plan(rewards)
    #pos = np.argwhere(rewards >= -50)
    max_indices = np.argmax(rewards, axis=1)
    print(rewards[max_indices[0]])
    pos = rewards[max_indices]
    print(pos)
    #%%
    a = np.array_split(pos, np.flatnonzero(np.diff(pos[:, 0])) + 1)
    # print(a)
    timestamp_action = []
    for i in a:
        print(i[0][0], np.argmax(i[:, 1]))
        timestamp_action.append((i[0][0], np.argmax(i[:, 1])))
    # timestamp_action = zip()
    # print(timestamp_action)
    # %%
    # TODO translate the outputs and figure out what to do with actions
    # print formated
    interval = 15
    mins = int(1440 / interval)
    intervals = np.linspace(0, 1440, mins)
    time_intervals = [str(timedelta(minutes=x)) for x in intervals]
    temps_const = np.arange(15, 25, 0.5)
    formated_timestamp_temp = [
        (time_intervals[x], str(temps_const[t]) + f"˚C") for x, t in timestamp_action
    ]
    pprint(formated_timestamp_temp)
    # TODO graf naucene veci po snizeni se mi zdaji fajn, rano divne (memorized z vecera asi)
    #%%
    fig, axs = plt.subplots(1, 1)
    d = np.arange(0, 96, 1)
    print(formated_timestamp_temp)
    only_temps = [temps_const[t] for _,t in timestamp_action]
    axs.plot(d, only_temps)
    current_values = axs.get_xticks()
    axs.set_xticklabels([str(timedelta(minutes=x * 15)) for x in current_values])
    axs.grid(True)
    # axs[0].set_xlim(str(timedelta(minutes=0)), str(timedelta(minutes=1440)))
    plt.show()
    #%%
    # analyze where is the setpoint action from the gained data 
    first = 0
    print("Actual feedback times: ", [str(timedelta(minutes=int(x)*15)) for x in np.array(feedback_days).flatten()])
    for i,x in enumerate(only_temps):
        if i == 0:
            first = x
        else:
            if first != x:
                print("setpoint: ",x, "C v", str(timedelta(minutes=x*15)))
                break
    pass

# %%
