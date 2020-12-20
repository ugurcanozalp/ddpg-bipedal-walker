import gym
import torch
import numpy as np
import matplotlib.pyplot as plt
from collections import deque
from td3_agent import TD3Agent
from fcn_train_test import train, test
from archs.mlp_models import Actor, Critic
import argparse
import os

model_type = "mlp"
rl_type = "td3"

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--flag", type=str, choices=['train', 'test'],
                    default='train', help="train or test?")
parser.add_argument("-e", "--env", type=str, choices=['classic', 'hardcore'],
                    default='classic', help="environment type, classic or hardcore?")
args = parser.parse_args()

if args.env == 'classic':
    env = gym.make('BipedalWalker-v3')
elif args.env == 'hardcore':
    env = gym.make('BipedalWalkerHardcore-v3')

agent = TD3Agent(Actor, Critic, state_size = env.observation_space.shape[-1], action_size=env.action_space.shape[-1])
env.seed(0)
print("Action dimension : ",env.action_space.shape)
print("State  dimension : ",env.observation_space.shape)
print("Action sample : ",env.action_space.sample())
print("State sample  : \n ",env.reset())    

if args.flag == 'train':   
    scores = train(env, agent, model_type=model_type)
    fig = plt.figure()
    ax = fig.add_subplot(111)
    plt.plot(np.arange(1, len(scores)+1), scores)
    plt.ylabel('Score')
    plt.xlabel('Episode #')
    plt.show()
    env.close()
elif args.flag == 'test':
    try:
        actor_file = os.path.join("models", rl_type, "_".join(["best", model_type, "actor.pth"]))
        critic_1_file = os.path.join("models", rl_type, "_".join(["best", model_type, "critic_1.pth"]))
        critic_2_file = os.path.join("models", rl_type, "_".join(["best", model_type, "critic_2.pth"]))
        agent.train_actor.load_state_dict(torch.load(actor_file, map_location={'cuda:0': 'cpu'}))
        agent.train_critic_1.load_state_dict(torch.load(critic_1_file, map_location={'cuda:0': 'cpu'}))
        agent.train_critic_2.load_state_dict(torch.load(critic_2_file, map_location={'cuda:0': 'cpu'}))
    except:
        actor_file = os.path.join("models", rl_type, "_".join(["last",model_type, "actor.pth"]))
        critic_1_file = os.path.join("models", rl_type, "_".join(["last", model_type, "critic_1.pth"]))
        critic_2_file = os.path.join("models", rl_type, "_".join(["last", model_type, "critic_2.pth"]))
        agent.train_actor.load_state_dict(torch.load(actor_file, map_location={'cuda:0': 'cpu'}))
        agent.train_critic_1.load_state_dict(torch.load(critic_1_file, map_location={'cuda:0': 'cpu'}))
        agent.train_critic_2.load_state_dict(torch.load(critic_2_file, map_location={'cuda:0': 'cpu'}))

    scores = test(env, agent)

    env.close()
else:
    print('Wrong flag!')