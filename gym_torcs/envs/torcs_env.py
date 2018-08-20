import gym
import numpy as np
import os
import time
from gym_torcs.gym_torcs.envs import snakeoil3_gym as snakeoil3
from gym import spaces


class TorcsEnv(gym.Env):
    damage = 0.
    metadata = {'render.modes': ['human']}
    global_step = 0

    def __init__(self, frame_skip=5, port=3001):
        self.port = port
        self.frame_skip = frame_skip
        high = np.array([ 1., 1., 1.])
        low  = np.array([-1., 0., 0.])
        self.action_space = spaces.Box(low=low, high=high, dtype=np.float32)
        high = np.concatenate((np.array([ np.pi,  np.inf,  np.inf,  1.]),
                              200.*np.ones(19)))  # angle speedX speedY trackPos track
        low  = np.concatenate((np.array([-np.pi, -np.inf, -np.inf, -1.]),
                              -200.*np.ones(19)))
        self.observation_space = spaces.Box(low=low, high=high,
                                            dtype=np.float32)

    def step(self, action):
        self.do_simulation(action, self.frame_skip)
        # prev_dist_raced= self.dist_raced
        prev_damage = self.damage
        ob = self._get_state()
        # self.dist_from_start = self.client.S.d["distFromStart"]
        self.dist_raced = self.client.S.d["distRaced"]
        self.damage = self.client.S.d["damage"]
        self.progress_check = np.roll(self.progress_check, 1)
        # self.progress_check[0] = self.dist_from_start  # prev_dist_raced
        self.progress_check[0] = self.dist_raced  # prev_dist_raced
        collision = prev_damage != self.damage
        reward = ob[1]*np.cos(ob[0]) if collision else -1  # DEEPMIND
        done = self._is_done(ob)
        # print('Reward:',self.reward,end=' ')
        self.time_step += 1
        self.global_step += 1
        self.total_reward += reward
        return ob, reward, done, {}

    def do_simulation(self, action, n_frames):
        self.client.R.d["steer"] = action[0]
        self.client.R.d["brake"] = action[1]
        self.client.R.d["accel"] = action[2]
        for _ in range(n_frames):
            self.client.respond_to_server()

    def _get_state(self):
        self.client.get_servers_input()
        raw_obs = self.client.S.d
        ob = np.array([raw_obs[sensor] for sensor in ['angle', 'speedX',
                                                      'speedY', 'trackPos']])
        ob = np.concatenate((ob, raw_obs['track']))
        return(ob)

    def _is_done(self, ob):
        # Episode terminates if nan value BUG
        # if np.isnan(self.dist_from_start):
        #     print('NAN Value')
        #     return True
        # Episode is terminated if no progress is made along the track after
        # 500 frames. #DEEPMIND
        # if self.dist_from_start - self.progress_check[-1] <= 0:
        if self.dist_raced - self.progress_check[-1] <= 0:
            print('no progress was made along the track after 500 frames: \
%d steps elapsed, reward: %d, global_step: %d, \
dist_raced: %f'
                  % (self.time_step, self.total_reward, self.global_step,
                     # self.dist_from_start))
                     self.dist_raced))
            return True
        return False

    def reset(self):
        self.time_step = 0
        self.total_reward = 0
        self.reset_torcs()
        self.client = snakeoil3.Client(self.port)
        ob = self._get_state()
        self.progress_check = -0.1 * np.ones(500)
        return ob

    def render(self, mode='human', close=False):
        pass

    def end(self):
        # os.system('pkill torcs')
        os.system('fuser -k %s/udp' % self.port)

    def reset_torcs(self):
        # os.system('pkill torcs')
        os.system('fuser -k %s/udp' % self.port)
        os.system('torcs -nodamage -nofuel -nolaptime -p %d -r \
                  $HOME/.torcs/config/raceman/quickrace.xml &' % self.port)


if __name__ == '__main__':
    env = gym.make('torcs-v0')
    print(env.port)
    # env.__init__(port=3002)
    # print(env.port)
    # exit(0)
    for i in range(10):
        o = env.reset()
        for j in range(1000):
            # action = np.array([0.,1.,0.])
            action = env.action_space.sample()
            start = time.time()
            o, r, d, i = env.step(action)
            end = time.time()
            print(end-start)
    env.end()
