# gym_torcs
An OpenAI gym environment fully compatible with OpenAI baselines implementation of various Deep Reinforcement Learning algorithms (DDPG,A2C,TRPO,PPO,ACER,ACKTR...).


## Requirements
This environment is intended to use the modified version of TORCS that I made:<br />
https://github.com/DamienLancry/blocking_torcs <br />
You will also need to 
``` 
pip install gym
```

## Getting Started
### Installation
```
git clone https://github.com/DamienLancry/gym_torcs
```
### Testing
```
python -m gym_torcs.gym_torcs.envs.torcs_env
```
## Aknowledgement
https://github.com/ugo-nama-kun/gym_torcs (For various reasons, this environment was not compatible with OpenAI baselines.)<br />
http://xed.ch/project/snakeoil/index.html
