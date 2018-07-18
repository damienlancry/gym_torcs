import gym
from gym import spaces
import numpy as np
import os
# os.chdir('/homes/drl17/Documents/Project/Torcs_Project/gym-torcs/')
from my_gym_torcs.envs import snakeoil3_gym as snakeoil3
import copy
import collections as col
import time
import numpy as np

class TorcsEnv(gym.Env):
    metadata = {'render.modes': ['human']}

    default_speed = 50

    initial_reset = True

    def __init__(self):
        self.initial_run  = True
        high = np.array([1.,1.,1.])
        low  = np.array([-1.,-1.,-1.])
        self.action_space = spaces.Box(low=low, high=high, dtype=np.float32)
        self.observation_space = spaces.Box(low=0., high=255., shape=(64,64,9), dtype=np.float32)

    def step(self, action): #takes 0.2 s => frameskip = 10
        self._take_action(action)
        prev_damage = self.state.damage
        self.state  = self._get_state()
        if self.state.damage > prev_damage:
            self.collision = -1
        else:
            self.collision = 0
        reward = self._get_reward()
        done   = self._is_done()
        self.ob_2 = self.ob_1
        self.ob_1 = self.ob
        self.ob   = self.state.img
        print(self.ob.shape)
        self.obs = np.concatenate([self.ob, self.ob_1, self.ob_2],axis=2)
        print(self.obs.shape)
        return self.obs, reward, done, {}

    def _take_action(self,action):
        self.client.R.d["steer"] = action[0]
        self.client.R.d["accel"] = action[1]
        self.client.R.d["brake"] = action[2]
        self.client.respond_to_server()

    def _get_reward(self):
        return self.state.speedX + self.collision # reward function from DEEPMIND

    def _get_state(self):
        self.client.get_servers_input()
        raw_obs = self.client.S.d
        names = ['focus',
                 'speedX', 'speedY', 'speedZ', 'angle',
                 'opponents',
                 'rpm',
                 'track',
                 'trackPos',
                 'wheelSpinVel',
                 'img',
                 'damage']
        Observation = col.namedtuple('Observation', names)
        # Get RGB from observation
        image_rgb = self.obs_vision_to_image_rgb(raw_obs['img'])
        return Observation(focus=np.array(raw_obs['focus'], dtype=np.float32)/200.,
                           speedX=np.array(raw_obs['speedX'], dtype=np.float32)/self.default_speed,
                           speedY=np.array(raw_obs['speedY'], dtype=np.float32)/self.default_speed,
                           speedZ=np.array(raw_obs['speedZ'], dtype=np.float32)/self.default_speed,
                           angle=np.array(raw_obs['angle'], dtype=np.float32)/3.1416,
                           opponents=np.array(raw_obs['opponents'], dtype=np.float32)/200.,
                           rpm=np.array(raw_obs['rpm'], dtype=np.float32),
                           track=np.array(raw_obs['track'], dtype=np.float32)/200.,
                           trackPos=np.array(raw_obs['trackPos'], dtype=np.float32)/1.,
                           wheelSpinVel=np.array(raw_obs['wheelSpinVel'], dtype=np.float32),
                           img=image_rgb,
                           damage = np.array(raw_obs['damage'], dtype=np.float32))

    def obs_vision_to_image_rgb(self, obs_image_vec):
        image_vec =  np.array(obs_image_vec,dtype=np.uint8)
        sz  = (64, 64)
        b   = np.flipud(image_vec[2:len(image_vec):3].reshape(sz))
        g   = np.flipud(image_vec[1:len(image_vec):3].reshape(sz))
        r   = np.flipud(image_vec[0:len(image_vec):3].reshape(sz))
        bgr = np.stack([b,g,r],axis=2)
        cv2.imshow('img', bgr)
        cv2.waitKey(0)
        return bgr

    def _is_done(self):
        self.client.R.d['meta'] =  np.cos(self.state.angle) < 0
        return self.client.R.d['meta']

    def reset(self,relauch=False):
        self.time_step = 0
        self.reset_torcs()
        self.client = snakeoil3.Client(p=3101, vision=True)
        self.state  = self._get_state()
        self.ob = self.ob_1 = self.ob_2 = self.state.img
        self.obs = np.concatenate([self.ob, self.ob_1, self.ob_2],axis=2)
        return self.obs

    def render(self, mode='human', close=False):
        pass

    def end(self):
        os.system('pkill torcs')

    def reset_torcs(self):
        os.system('pkill torcs')
        time.sleep(0.5)
        os.system('torcs -nofuel -nolaptime -vision &')
        time.sleep(0.5)
        os.system('sh autostart.sh')
        time.sleep(0.5)
