#https://www.researchgate.net/publication/320296763_Recurrent_Network-based_Deterministic_Policy_Gradient_for_Solving_Bipedal_Walking_Challenge_on_Rugged_Terrains
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import gym
import random
from .utils.stable_transformer import PositionalEncoding, LearnablePositionalEncoding, StableTransformerLayer, TransformerEncoder
from torch.distributions import Normal

EPS = 0.003

class StableTransformerEncoder(nn.Module):

    def __init__(self, d_in, d_model, nhead, dim_feedforward=192, dropout=0.1, seq_len=16):
        super(StableTransformerEncoder,self).__init__()
        #self.embedding_scale = d_model**0.5
        self.inp_embedding = nn.Sequential(nn.Linear(d_in, d_model), nn.LayerNorm(d_model), nn.Tanh()) # 
        nn.init.xavier_uniform_(self.inp_embedding[0].weight, gain=nn.init.calculate_gain('tanh')) #
        nn.init.zeros_(self.inp_embedding[0].bias) 
        self.pos_embedding = PositionalEncoding(d_model, seq_len=seq_len)
        self.encoder = StableTransformerLayer(d_model, nhead, dim_feedforward, dropout, only_last_state=True)
        #self.encoder = nn.Sequential(
        #    StableTransformerLayer(d_model, nhead, dim_feedforward, dropout), 
        #    StableTransformerLayer(d_model, nhead, dim_feedforward, dropout, only_last_state=True)
        #)

    def forward(self, src):
        x = src
        x = self.inp_embedding(x)
        #x = x * self.embedding_scale
        x = self.pos_embedding(x)
        x = self.encoder(x)  # batch, seq, emb
        x = x[:, -1]
        return x

class Critic(nn.Module):

    def __init__(self, state_dim=24, action_dim=4):
        """
        :param state_dim: Dimension of input state (int)
        :param action_dim: Dimension of input action (int)
        :return:
        """
        super(Critic, self).__init__()

        self.state_dim = state_dim
        self.action_dim = action_dim
        
        self.state_encoder = StableTransformerEncoder(d_in=self.state_dim,
            d_model=96, nhead=4, dim_feedforward=256, dropout=0.0)

        self.fc2 = nn.Linear(96 + self.action_dim, 128)
        nn.init.xavier_uniform_(self.fc2.weight, gain=nn.init.calculate_gain('relu'))
        
        self.fc_out = nn.Linear(128,1, bias=True)
        #nn.init.xavier_uniform_(self.fc_out.weight)
        nn.init.uniform_(self.fc_out.weight, -0.003,+0.003)
        self.fc_out.bias.data.fill_(0.0)

        self.act = nn.PReLU(128)

    def forward(self, state, action):
        """
        returns Value function Q(s,a) obtained from critic network
        :param state: Input state (Torch Variable : [n,state_dim] )
        :param action: Input Action (Torch Variable : [n,action_dim] )
        :return: Value function : Q(S,a) (Torch Variable : [n,1] )
        """
        s = self.state_encoder(state)
        x = torch.cat((s,action),dim=1)
        x = self.act(self.fc2(x))
        x = self.fc_out(x)*10
        return x


class Actor(nn.Module):

    def __init__(self, state_dim=24, action_dim=4, stochastic=False):
        """
        :param state_dim: Dimension of input state (int)
        :param action_dim: Dimension of output action (int)
        :param action_lim: Used to limit action in [-action_lim,action_lim]
        :return:
        """
        super(Actor, self).__init__()

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.stochastic = stochastic
        
        self.state_encoder = StableTransformerEncoder(d_in=self.state_dim,
            d_model=96, nhead=4, dim_feedforward=192, dropout=0.0)

        self.fc = nn.Linear(96,action_dim)
        nn.init.uniform_(self.fc.weight, -0.003,+0.003)
        nn.init.zeros_(self.fc.bias)

        if self.stochastic:
            self.log_std = nn.Linear(96, action_dim)
            nn.init.uniform_(self.log_std.weight, -0.003,+0.003)
            nn.init.zeros_(self.log_std.bias)  
            
        self.tanh = nn.Tanh()

    def forward(self, state, explore=True):
        """
        returns either:
        - deterministic policy function mu(s) as policy action.
        - stochastic action sampled from tanh-gaussian policy, with its entropy value.
        this function returns actions lying in (-1,1) 
        :param state: Input state (Torch Variable : [n,state_dim] )
        :return: Output action (Torch Variable: [n,action_dim] )
        """
        s = self.state_encoder(state)
        if self.stochastic:
            means = self.fc(s)
            log_stds = self.log_std(s)
            log_stds = torch.clamp(log_stds, min=-10.0, max=2.0)
            stds = log_stds.exp()
            dists = Normal(means, stds)
            if explore:
                x = dists.rsample()
            else:
                x = means
            actions = self.tanh(x)
            log_probs = dists.log_prob(x) - torch.log(1-actions.pow(2) + 1e-6)
            entropies = -log_probs.sum(dim=1, keepdim=True)
            return actions, entropies

        else:
            actions = self.tanh(self.fc(s))
            return actions
