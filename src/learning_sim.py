# %%
from events import nearest_pointfive, get_exp_temp_values, generate_cold_requests
from utils import find_nearest, temperature_to_index, index_to_temperature, bcolors
from sim_user import SimUser
from sim_temperature import SimTemperature
from myenum.action import TemperatureAction
import numpy as np
import random
import matplotlib.pyplot as plt
import math
from datetime import timedelta
from statistics import mean
from pprint import pprint

actions = ["increase", "decrease"]
# mathematical formulas, needs work
APPROACH_1 = False
# for generic room, not learing friendly
APPROACH_2 = False
# reward high if feedback was long time ago
APPROACH_3 = True

# TODO action enum


def get_rewards(temperature_days: np.array, feedback_days):
    return calc_reward_for_states(temperature_days, feedback_days)
    # q_arr = m = np.zeros((96, 2))
    # TODO


def calc_reward_for_states(temperature_days, feedback_days) -> np.array:
    # calculation using custom reward function conditions and formulas
    rewards = np.zeros((96, 20))
    temps_const = np.arange(15, 25.5, 0.5)
    beta = 10
    alpha = 0.2
    sigma = 0.2
    for days_sum,temperature_day in enumerate(temperature_days):
        for delta_index, state in enumerate(temperature_day):
            for i, t in enumerate(temps_const):          
                # S: 24/06/2023
                if APPROACH_2:
                    s = rewards_simple(state, delta_index, feedback_days, t)
                    if days_sum > 0:
                        rewards[delta_index, i] = round(mean([rewards[delta_index, i], s]),0)
                    #s *= sigma
                    else:
                        rewards[delta_index, i] = s
               
                if APPROACH_1:
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
    # TODO all days
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
            if temperature_delta >=2: reward = -36
            if temperature_delta ==1: reward = -36
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -12
    # feedback bude az za vic nez dva intervaly
    if delta < -2:
        if action=="increase":
            if temperature_delta >=2: reward = -36
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 0
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -36
        else:
            if temperature_delta >=2: reward = -36
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 0
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -36
    if delta == -2:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 0
            if temperature_delta ==-1: reward = 12
            if temperature_delta <=-2: reward = 36
        else:
            if temperature_delta >=2: reward = 36
            if temperature_delta ==1: reward = 12
            if temperature_delta ==0: reward = 0
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -12
    if delta == -1:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = 36
            if temperature_delta <=-2: reward = 0
        else:
            if temperature_delta >=2: reward = 0
            if temperature_delta ==1: reward = 36
            if temperature_delta ==0: reward = 12
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -12
    if delta == 0:
        if action=="increase":
            if temperature_delta >=2: reward = -12
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 36
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -36
        else:
            if temperature_delta >=2: reward = -36
            if temperature_delta ==1: reward = -12
            if temperature_delta ==0: reward = 36
            if temperature_delta ==-1: reward = -12
            if temperature_delta <=-2: reward = -12
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
    # TODO presence
    # derivace, cas, teplota
    # TODO few historical states
    #print(f"starting at {historical_temps[-1]}˚C")
    return 0,0


def is_positively_rewarded(time_index, temperature_index, rewards):
    # TODO now just -10
    if rewards[time_index, temperature_index] <= 0:
        return False
    else:
        return True


def get_next_temperature_action(temperature_derivative, time_index, temperature_index, epsilon, idling, q_values):
    if np.random.random() < epsilon:
        if np.amax(q_values[time_index, temperature_index,temperature_derivative+1]) < 0:
        #if np.amax(q_values[time_index, temperature_index]) < 0:
            if np.random.random() > idling:
                return TemperatureAction.KEEP.value
        return np.argmax(q_values[time_index, temperature_index, temperature_derivative+1])
        #return np.argmax(q_values[time_index, temperature_index])
    else:
        return np.random.randint(2)


def perform_temperature_action(temperature_exp_step, temp_derivative, current_temperature_index,
                               action: int, Temperature_Evaluator : SimTemperature, log=False):
    # action "-1" keeps same temperature
    new_temperature_index = current_temperature_index
    new_temp_derivative = temp_derivative
    reset_exponential_increase = False
    # pause heating
    if keep_or_opposite_action_of_derivative(temp_derivative, action):
        new_temp_derivative = 0
        reset_exponential_increase = True
    # start heating in the process of cooling down (pause cooling)
    elif ((action == TemperatureAction.INCREASE.value and action != TemperatureAction.DECREASE.value) or temp_derivative==1) and current_temperature_index != 20:
        # heating
        #new_temperature_index += 1
        new_temperature_index = temperature_to_index(
            Temperature_Evaluator.next_temperature(
                index_to_temperature(current_temperature_index), temperature_exp_step
            )
        )
        if log:
            print(f"New temperature index: {new_temperature_index} after {current_temperature_index}", end=" ")
        new_temp_derivative = 1
    elif ((action == TemperatureAction.DECREASE.value and action != TemperatureAction.INCREASE.value) or temp_derivative==-1) and current_temperature_index != 0:
        # turn off heating
        new_temperature_index = temperature_to_index(
            Temperature_Evaluator.next_temperature(
                index_to_temperature(current_temperature_index), temperature_exp_step, is_decrease=True
            )
        )
        new_temp_derivative = -1
    
        
    # exponential increase/decrease done or upper/bottom bound reached
    if temperature_exp_step == 5 or (new_temperature_index == 20):
        reset_exponential_increase = True
        return reset_exponential_increase, new_temperature_index, 0
    
    return reset_exponential_increase, new_temperature_index, new_temp_derivative

def keep_or_opposite_action_of_derivative(temp_derivative, action):
    return ((action == TemperatureAction.INCREASE.value and temp_derivative == -1)
        or (action == TemperatureAction.KEEP.value)
        or (action == TemperatureAction.DECREASE.value and temp_derivative == 1))


def create_plan(
    current_temperature : float,
    q_table,
    User : SimUser,
    TemperatureEnvironment : SimTemperature,
    mode="model_only"
    ):
    temperature_derivative, current_time_index = get_starting_state()
    current_temperature_index = temperature_to_index(current_temperature)
    #time_actions = []
    new_temperature_plan = np.zeros((96,1))
    step = 0
    last_action = None
    second_to_last_action = None
    happy_counter = 0
    last_unexpected_action_time = -128
    never_ask_again = False
    input_action = None
    while not current_time_index == 96:
        #if 70 <= current_time_index <= 73:
        #    for i in range(3):
            #print(np.argmax(q_table[current_time_index,current_temperature_index,i]))
        #    pass
        # simualting our inputs
        # to insert console inputs or HASS inputs
        if last_unexpected_action_time+3 < current_time_index:
            prioritize = False
            input_action = None
        if current_time_index % 4 == 0 and mode != "model_only" and not never_ask_again:
            input_action, never_ask_again = get_user_live_input(mode, current_time_index, current_temperature_index)
            if input_action == 0 or input_action == 1:
                last_unexpected_action_time = current_time_index
        if input_action is not None:
            prioritize = True
                    
        
        new_temperature_plan[current_time_index] = index_to_temperature(current_temperature_index)
        print(f"TIME: {current_time_index}", end=" ")
        print(f"TEMPERATURE: {bcolors.BOLD}{index_to_temperature(current_temperature_index)}{bcolors.ENDC} ", end=" ")
        user_request = User.get_user_request_per_timeframe(current_time_index,current_temperature_index,tolerance=1.)
        if user_request and temperature_derivative != 0:
            print(f"IGNORED REQUEST DURING CHANGE", end=" ")
            happy_counter +=1
        if user_request is not None:
            print(f"{bcolors.WARNING}MODEL USER UNHAPPY <{user_request.value}> {bcolors.ENDC}", end=" ")
        else:
            print("NO REQUEST", end=" ")
            happy_counter += 1
        if prioritize == False:
            action = get_next_temperature_action(temperature_derivative,current_time_index, current_temperature_index,1.,1.,q_table)
        else:
            action = input_action
        if is_repeating(last_action, second_to_last_action, action) and prioritize == False:
            print(f"{bcolors.OKCYAN}REPEATING DETECTED!{bcolors.ENDC}", end=" ")
            if action == TemperatureAction.INCREASE.value:
                action = TemperatureAction.KEEP.value
            if action == TemperatureAction.DECREASE.value:
                action = TemperatureAction.KEEP.value
        print(f"ACTION: {action}", end=" ")
        flag, current_temperature_index, temperature_derivative = perform_temperature_action(
            step, temperature_derivative,current_temperature_index,action,
            TemperatureEnvironment
            )
        second_to_last_action = last_action
        last_action = action

        if action == TemperatureAction.INCREASE.value and (temperature_derivative == 0 or temperature_derivative == 1):
            print(f"{bcolors.FAIL}>>INCREASING>>{bcolors.ENDC}", end=" ")
        elif action == TemperatureAction.DECREASE.value and (temperature_derivative == 0 or temperature_derivative == -1):
            print(f"{bcolors.OKBLUE}<<DECREASING<<{bcolors.ENDC}", end=" ")
        else:
            print(f"==KEEPING==", end=" ")
                    
        if flag:
            step = 0
        else:
            step += 1
        print(f"DER: {temperature_derivative}")
        #time_actions.append([current_time_index,action])
        current_time_index += 1
    #return time_actions
    print(f"Inhabitant is happy {round(happy_counter*100/96,2)}% of the day.")
    return new_temperature_plan

def get_user_live_input(mode, current_time_index, current_temperature_index):
    input_action = None
    never_ask_again = False
    if mode == "developer":
        print(f"Do you like current temperature? ({index_to_temperature(current_temperature_index)}˚C"+
                      f" at {str(timedelta(minutes=int(current_time_index) * 15))})")
        print(f"Type [k] = no changes, [+] = increase, [-] = decrease, [f] = never ask again")
        while True:
            input_str = str(input())
            if input_str == "k":
                break
            if input_str == "+":
                input_action = 0
                break
            if input_str == "-":
                input_action = 1
                break
            if input_str == "f":
                never_ask_again = True
                break
            print(f"Wrong format. Type [k] to do no changes.")
    return input_action, never_ask_again
    

def training(
    temperature : float,
    User : SimUser,
    TemperatureEnvironment : SimTemperature,
    rewards=None ) -> np.ndarray:
    # TODO derivative in q table
    #q_table = np.zeros((96, 21, 3, 3))
    q_table = np.random.rand(96, 21, 3, 3)
    #q_table = np.zeros((96, 21, 2))
    
    epsilon = 0.8
    #inverse
    idling = 0.6
    discount_factor = 0.2
    learning_rate = 0.99
    # TODO perform just increase action and in few next steps keep increasing temperature and returning 
    # positive derivative/or negative for decrease
    # remove hardcoded temperature from perform, ignore request  in the process of increase
    last_user_request_type = None
    for episode in range(2000):
        # starting time and temperature
        #print(episode)
        temperature_derivative, time_index = get_starting_state()
        temperature_index = temperature_to_index(temperature)
        # choose between positively rewarded states
        # TODO new learning, derivative
        starting_time = time_index
        last_request_time_index = -1
        temperature_change_step = 0
        #while not is_positively_rewarded(time_index, temperature_index, rewards):
        last_action = None
        second_to_last_action = None
        while True:
                
            #if time_index==34:
            #    print(temperature_index)
            # choose action
            #user_interputions = []
            #print(time_index, temperature_index)
            #print(type(time_index), type(temperature_index))
            
            q_action = get_next_temperature_action(
                    temperature_derivative,time_index, temperature_index, epsilon, idling, q_table
                )
            # e.g. we need to stop it from doing increase action if last 
            # one was decrease and before that increase, so do different
            # action then evaluating in q_table
            if is_repeating(last_action, second_to_last_action, q_action):
                if q_action == TemperatureAction.INCREASE.value:
                    real_action = TemperatureAction.KEEP.value
                if q_action == TemperatureAction.DECREASE.value:
                    real_action = TemperatureAction.KEEP.value
            else:
                real_action = q_action
                    
            old_temperature_index = temperature_index
            old_temperature_derivative = temperature_derivative

            change_complete_flg, temperature_index, temperature_derivative = perform_temperature_action(
                temperature_change_step, 
                temperature_derivative, temperature_index, real_action,
                TemperatureEnvironment
            )
            second_to_last_action = last_action
            last_action = q_action
            time_index += 1
            if change_complete_flg:
                temperature_change_step = 0
            else:
                temperature_change_step += 1
            # TODO Rewarding action ?
            user_request = User.get_user_request_per_timeframe(time_index,temperature_index)
                
            if last_user_request_type is None:
                last_user_request_type = user_request
                
            # derivative used basically for ignoring repeating requests
            # TODO there still can be first user request while changing temperature
            # TODO learning doesnt know which way its action was wrong?
            penalty = -10
            # if we received request during "calm phase" (while not changing temperature)
            
            #if user_request is not None and temperature_derivative == 0:
                #user_interputions.append((time_index, temperature_index))
            #    penalty = -500.0
            #    last_request_time_index = time_index
            
            # BAD ! RL started chaning actions afap
            if user_request is not None and user_request != last_user_request_type:
                penalty = -300
                last_user_request_type = user_request
                last_request_time_index = time_index
            elif user_request is not None:
                penalty = -500
                last_request_time_index = time_index
                last_user_request_type = user_request
            elif user_request is None:
                penalty = calc_request_delta_penalty(last_request_time_index, time_index)
                #print(penalty)
            # agent attempting out of bounds actions
            if q_action == TemperatureAction.INCREASE.value and temperature_index >= 20:
                penalty = -1000
            elif q_action == TemperatureAction.DECREASE.value and temperature_index == 0:
                penalty = -1000
            #print("penalty:", penalty)
            ####reward = rewards[time_index, temperature_index]
            # calculate temporal difference
            old_q_value = q_table[time_index, old_temperature_index, old_temperature_derivative+1, q_action]
            #old_q_value = q_table[time_index, old_temperature_index, action]
            # TODO look into this
            temporal_difference = penalty + (
                discount_factor * np.max(q_table[
                    time_index,
                    temperature_index,
                    temperature_derivative+1
                    ])
            )
            #print(f"TD: {temporal_difference}")
            #print(np.unique(q_table[66,17,1]))
            # update q for previous state acton pair
            new_q_value = old_q_value + (learning_rate * temporal_difference)
            
            #if old_q_value < new_q_value:
            #    print("new better")
            #if old_q_value > new_q_value:
            #    print("old better")
            
            # +1 for derivative indexing
            q_table[time_index, old_temperature_index,old_temperature_derivative+1, q_action] = new_q_value
            #q_table[time_index, old_temperature_index, action] = new_q_value

            # move to next time interval
            #print("time_index", time_index)
            if time_index == 95:
                #if episode == 999:
                    #print(f"User requests in last episode: {user_interputions}")
                # one day learning reached
                #if user_interputions:
                    # TODO Q_table saving, data processing
                #    with open("q_tables.txt", "a") as f:
                #        print(q_table, file=f)
                #        print("\n\n\n", file=f)
                break
                #time_index += 1
                # 24h reached
                #if time_index == starting_time:
                #    break
            
                
    print(np.unique(q_table))
    print("Day strategy learnt")
    return q_table

def is_repeating(last_action, second_to_last_action, action):
    return second_to_last_action == action and action != last_action and second_to_last_action != 2 and last_action != 2
    
    
def calc_request_delta_penalty(last_request_time_index, time_index) -> int:
    # !! method doesnt work if feedback was received right now !!
    # was last request received just less than x hours before?

    # ideal would be not increasing or decreasing temperature rapidly anymore when user doesnt complain
    # logical interpretation: 
    penalty = 50+round((20*(((math.log((time_index-last_request_time_index),10)-0.301)/10))-0.1),2)
    #penalty = int(round(((time_index - last_request_time_index)/4)*(6/5)))
    if penalty <= 1:
        print(f"penalty: {time_index} - {last_request_time_index}: [{penalty}]")
    return penalty


def get_plan(rewards: np.array):
    pos = np.argwhere(rewards >= 0)
    print(pos)
    for i, j in pos:
        print(i, j)


if __name__ == "__main__":
    pass

# %%
