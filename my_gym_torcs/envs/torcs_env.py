import gym
from gym import spaces
import numpy as np
import os
os.chdir('/homes/drl17/Documents/Project/Torcs_Project/gym-torcs/')
from my_gym_torcs.envs import snakeoil3_gym as snakeoil3
import copy
import collections as col
import time
import numpy as np

class TorcsEnv(gym.Env):
    metadata = {'render.modes': ['human']}
    speed_limit          = 5
    speed_limit_checking = 100

    def __init__(self):
        self.initial_run  = True
        high = np.array([1.,1.,1.])
        low  = np.array([-1.,0.,-1.])
        self.action_space      = spaces.Box(low=low, high=high, dtype=np.float32)
        self.observation_space = spaces.Box(low=0., high=1., shape=(64,64,9), dtype=np.float32)

    def step(self, action): #takes 0.2 s => frameskip = 10
        self._take_action(action)
        prev_damage = self.state.damage
        self.state  = self._get_state()
        if self.state.damage > prev_damage:
            self.collision = -1
            print('COLLISION')
        else:
            self.collision = 0
        self.reward = self._get_reward()
        done   = self._is_done()
        self.time_step += 1
        self.ob_2 = self.ob_1
        self.ob_1 = self.ob
        self.ob   = self.state.img
        self.obs = np.concatenate([self.ob, self.ob_1, self.ob_2],axis=2)
        return self.obs, self.reward, done, {}

    def _take_action(self,action):
        self.client.R.d["steer"] = action[0]
        self.client.R.d["accel"] = action[1]
        self.client.R.d["brake"] = action[2]
        self.client.respond_to_server()

    def _get_reward(self):
        return self.state.speedX*np.cos(self.state.angle) + self.collision # reward function from DEEPMIND

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
                           speedX=np.array(raw_obs['speedX'], dtype=np.float32),
                           speedY=np.array(raw_obs['speedY'], dtype=np.float32),
                           speedZ=np.array(raw_obs['speedZ'], dtype=np.float32),
                           angle=np.array(raw_obs['angle'], dtype=np.float32),
                           opponents=np.array(raw_obs['opponents'], dtype=np.float32)/200.,
                           rpm=np.array(raw_obs['rpm'], dtype=np.float32),
                           track=np.array(raw_obs['track'], dtype=np.float32)/200.,
                           trackPos=np.array(raw_obs['trackPos'], dtype=np.float32),
                           wheelSpinVel=np.array(raw_obs['wheelSpinVel'], dtype=np.float32),
                           img=image_rgb,
                           damage = np.array(raw_obs['damage'], dtype=np.float32))

    def obs_vision_to_image_rgb(self, obs_image_vec):
        image_vec =  np.array(obs_image_vec)/255. # deepmind preprocessing
        sz  = (64, 64)
        b   = np.flipud(image_vec[2:len(image_vec):3].reshape(sz))
        g   = np.flipud(image_vec[1:len(image_vec):3].reshape(sz))
        r   = np.flipud(image_vec[0:len(image_vec):3].reshape(sz))
        bgr = np.stack([b,g,r],axis=2)
        return bgr

    def _is_done(self):
        # Episode terminates if car running backward
        if self.speed_limit_checking < self.time_step and self.state.speedX < 0:
            print('CAR RUNNING BACKWARD')
            # self.client.R.d['meta'] = 1
            return True
        # Episode is terminated if the car is out of the track
        if abs(self.state.trackPos) > 1:
            print('OUT OF TRACK')
            self.reward = -100
            # self.client.R.d['meta'] = 1
            return True
        # Episode terminates if the car is not driving fast enough
        if self.speed_limit_checking < self.time_step:
            speed = np.sqrt(self.state.speedX**2 + self.state.speedY**2)
            if speed < self.speed_limit:
                print("NO PROGRESS")
                self.reward = -100
                # self.client.R.d['meta'] = 1
                return True
        return False

    def reset(self):
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

    def suspend(self):
        os.system('sh autosuspend.sh')
        time.sleep(0.5)

    def resume(self):
        os.system('sh autosuspend.sh')
        time.sleep(0.5)
