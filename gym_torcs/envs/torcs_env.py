import gym
import numpy as np
import os
import time
from gym_torcs.gym_torcs.envs import snakeoil3_gym as snakeoil3
from gym import spaces


class TorcsEnv(gym.Env):
    global_step = 0

    def __init__(self, frame_skip=5, port=3001):
        self.port       = port
        self.frame_skip = frame_skip
        high = np.array([ 1., 1., 1.])
        low  = np.array([-1., 0., 0.])
        self.action_space      = spaces.Box(low=low, high=high, dtype=np.float32)
        high = np.concatenate((np.array([ np.pi,  np.inf,  np.inf,  1.]), 200.*np.ones(19)))  # angle speedX speedY trackPos track
        low  = np.concatenate((np.array([-np.pi, -np.inf, -np.inf, -1.]),  -1.*np.ones(19)))
        self.observation_space = spaces.Box(low=low, high=high, dtype=np.float32)

    def step(self, action):
        self.do_simulation(action, self.frame_skip)
        ob           = self._get_state()
        reward       = ob[1]*np.cos(ob[0])
        done         = abs(ob[3]) > 1
        self.ret    += reward
        self.time_step+= 1
        return ob, reward, done, {}

    def do_simulation(self, action, n_frames):
        self.client.R.d["steer"] = action[0]
        self.client.R.d["accel"] = action[1]
        self.client.R.d["brake"] = action[2]
        for _ in range(n_frames):
            self.client.respond_to_server()

    def _get_state(self):
        self.client.get_servers_input()
        raw_obs = self.client.S.d
        ob = np.array([raw_obs[sensor] for sensor in ['angle', 'speedX', 'speedY', 'trackPos']])
        ob = np.concatenate((ob, raw_obs['track']))
        return(ob)

    def reset(self):
        self.reset_torcs()
        self.client = snakeoil3.Client(self.port)
        self.time_step = 0
        self.ret       = 0
        ob = self._get_state()
        return ob

    def reset_torcs(self):
        os.system('fuser -s -k %s/udp' % self.port)
        os.system('torcs -nodamage -nofuel -nolaptime -p %d -r \
                  $HOME/.torcs/config/raceman/quickrace.xml &' % self.port)

    def close(self):
        os.system('fuser -s -k %s/udp' % self.port)


if __name__ == '__main__':
    env = gym.make('Torcs-v0')
    for i in range(10):
        o = env.reset()
        for j in range(100):
            action = env.action_space.sample()
            start = time.time()
            o, r, d, i = env.step(action)
            end = time.time()
            print(end-start)
    env.close()
