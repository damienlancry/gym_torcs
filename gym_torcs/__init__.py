from gym.envs.registration import register

register(
    id='Torcs-v0',
    entry_point='gym_torcs.gym_torcs.envs:TorcsEnv',
)
