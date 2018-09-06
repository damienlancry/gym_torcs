import gym
import numpy as np
import os
import time
from gym_torcs.gym_torcs.envs import snakeoil3_gym as snakeoil3
from gym import spaces


class TorcsEnv(gym.Env):
    ob = np.empty((19,))
    damage = 0.
    metadata = {'render.modes': ['human']}
    global_step = 0

    def __init__(self, frame_skip=5, port=3001):
        self.port = port
        self.frame_skip = frame_skip
        high = np.array([ 1.])  # , 1.])  # , 1.])
        low  = np.array([-1.])  # , 0.])  # , 0.])
        self.action_space = spaces.Box(low=low, high=high, dtype=np.float32)
        high = np.concatenate((np.array([ np.pi,  np.inf,  np.inf,  1.]), 200.*np.ones(19)))  # angle speedX speedY trackPos track
        low  = np.concatenate((np.array([-np.pi, -np.inf, -np.inf, -1.]),-200.*np.ones(19)))
        self.observation_space = spaces.Box(low=low, high=high,
                                            dtype=np.float32)

    def step(self, action):
        self.do_simulation(action, self.frame_skip)
        prev_ob = self.ob
        prev_dist_raced = self.dist_raced
        self.ob = self._get_state()
        if np.isnan(self.ob).any():
            return prev_ob, self.reward, True, {}
        done = self._is_done()
        self.dist_raced = self.client.S.d["distRaced"]  # - self.offset
        self.reward = self.dist_raced - prev_dist_raced # ob[1]*np.cos(ob[0])  # if no_collision else -1  # DEEPMIND
        self.reward = self.dist_raced - prev_dist_raced # ob[1]*np.cos(ob[0])  # if no_collision else -1  # DEEPMIND
        self.time_step += 1
        self.global_step += 1
        self.total_reward += self.reward
        self.progress_check = np.roll(self.progress_check, 1)
        self.progress_check[0] = self.total_reward
        return self.ob, self.reward, done, {}

    def do_simulation(self, action, n_frames):
        self.client.R.d["steer"] = action[0]
        # self.client.R.d["accel"] = action[1]
        # self.client.R.d["brake"] = action[1]
        for _ in range(n_frames):
            self.client.respond_to_server()

    def _get_state(self):
        self.client.get_servers_input()
        raw_obs = self.client.S.d
        ob = np.array([raw_obs[sensor] for sensor in ['angle', 'speedX', 'speedY', 'trackPos']])
        ob = np.concatenate((ob, raw_obs['track']))
        return(ob)

    def termination_message(self):
        print("time_steps %d, global_step: %d, dist_raced: %f" % (self.time_step, self.global_step, self.total_reward))

    def _is_done(self):
        if abs(self.client.S.d['trackPos']) > 1:
            print("OUT OF TRACK: ",end = "")
            self.termination_message()
            return True
        if self.dist_raced - self.progress_check[-1] <= 0:
            print("no progress along the track after 500 frames: ",end = "")
            self.termination_message()
            return True
        if self.dist_raced >= 5784:
            print("lap Completed ",end = "")
            self.termination_message()
            return True
        if self.time_step >= 30000:  # In order to have more episodes
            print("Taking too much Time to complete race: ",end = "")
            self.termination_message()
            return True
        return False

    def reset(self):
        self.reset_torcs()
        self.client = snakeoil3.Client(self.port)
        # self.seed()
        # self.reset_race()
        # self.offset = 0  # self.client.S.d["distRaced"]
        self.time_step = 0
        self.total_reward = 0
        self.dist_raced = 0
        self.progress_check = -0.1 * np.ones(500)
        ob = self._get_state()

        return ob

    # def seed(self,seed=None):
        # self.random_seed =  np.random.randint(low=0, high=12000) if seed is None else seed

    def reset_race(self):
        for i in range(self.random_seed):
                self.client.get_servers_input()
                snakeoil3.drive_example(self.client)
                self.client.respond_to_server()

    def reset_torcs(self):
        os.system('fuser -s -k %s/udp' % self.port)
        os.system('torcs -nodamage -nofuel -nolaptime -p %d -r \
                  $HOME/.torcs/config/raceman/quickrace.xml &' % self.port)

    def render(self, mode='human', close=False):
        pass

    def close(self):
        os.system('fuser -s -k %s/udp' % self.port)


if __name__ == '__main__':
    env = gym.make('torcs-v0')
    for i in range(10):
        o = env.reset()
        for j in range(100):
            action = env.action_space.sample()
            start = time.time()
            o, r, d, i = env.step(action)
            end = time.time()
            print(end-start)
    env.close()
