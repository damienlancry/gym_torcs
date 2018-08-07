import gym
import numpy as np
import os
import collections as col
import time
import threading
import subprocess
from gym_torcs.gym_torcs.envs import snakeoil3_gym as snakeoil3
from gym import spaces

class TorcsEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    speed_limit          = 5
    speed_limit_checking = 100

    def __init__(self):
        self.initial_run  = True
        high = np.array([ 1.,1.,.5])
        low  = np.array([-1.,0.,0.])
        self.action_space      = spaces.Box(low=low, high=high, dtype=np.float32)
        high = np.array([ np.pi,  np.inf,  np.inf,  1.])#angle speedX speedY trackPos
        low  = np.array([-np.pi, -np.inf, -np.inf, -1.])
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)


    def step(self, action):
        self._take_action(action)
        ob     = self._get_state()
        reward = ob[1]*np.cos(ob[0])
        done   = self._is_done(ob   )
        self.time_step += 1
        return ob, reward, done, {}

    def _take_action(self,action):
        self.client.R.d["steer"] = action[0]
        self.client.R.d["accel"] = action[1]
        self.client.R.d["brake"] = action[2]
        self.client.respond_to_server()

    def _get_state(self):
        self.client.get_servers_input()
        raw_obs=self.client.S.d
        ob = np.array([raw_obs[sensor] for sensor in ['angle','speedX','speedY','trackPos']])
        return(ob)

    def _is_done(self,ob):
        # Episode terminates if car running backward
        if np.cos(ob[0]) < -1/2:
            print('CAR RUNNING BACKWARD')
            return True
        # Episode is terminated if the car is out of the track
        if abs(ob[-1]) > 1:
            print('OUT OF TRACK')
            # self.reward = -100
            return True
        return False

    def reset(self):
        self.time_step = 0
        self.reset_torcs()
        self.client = snakeoil3.Client(p=3001, vision=False)
        print('bite')
        ob          = self._get_state()
        return ob

    def render(self, mode='human', close=False):
        pass

    def end(self):
        os.system('pkill torcs')

    def reset_torcs(self):
        os.system('pkill torcs')
        os.system('torcs -nodamage -nofuel -nolaptime -r /home/lancry/.torcs/config/raceman/quickrace.xml &')
        # time.sleep(.001)


if __name__ == '__main__':
    env = gym.make('torcs-v0')
    for i in range(1):
        o = env.reset()
        for j in range(1000):
            # action = np.array([0.,1.,0.])
            action = env.action_space.sample()
            start = time.time()
            o,r,d,i = env.step(action)
            end = time.time()
            print(end-start)
    env.end()
