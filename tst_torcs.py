import my_gym_torcs
import gym
import time
import numpy as np

env = gym.make('torcs-v0')

max_ep = 2
max_t  = 1000
for ep in range(max_ep):
    obs = env.reset()
    for t in range(max_t):
        action = np.array([1,1,0])
        start = time.time()
        obs, reward, done, info = env.step(action)
        end = time.time()
        print(end - start)
        if done: break



env.end()
