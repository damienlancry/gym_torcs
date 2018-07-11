import my_gym_torcs
import gym
import time


env = gym.make('torcs-v0')

max_ep = 1
max_t  = 50
for ep in range(max_ep):
    obs = env.reset()
    for t in range(max_t):
        print t
        action = env.action_space.sample()
        start = time.time()
        obs, reward, done, info = env.step(action)
        end = time.time()
        print end - start
        if done: break



env.end()
