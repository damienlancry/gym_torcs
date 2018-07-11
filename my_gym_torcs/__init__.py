from gym.envs.registration import register

register(
    id='torcs-v0',
    entry_point='my_gym_torcs.envs:TorcsEnv',
)
