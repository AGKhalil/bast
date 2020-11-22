"""Base agent class which handles interacting with the environment for
generating experience
"""
from typing import Tuple

import gym3
import numpy as np
from collections import defaultdict
import torch
import torch.nn as nn
import torch.nn.functional as F

from squiRL.common.data_stream import Experience


class Agent:
    """
    Base Agent class handling the interaction with the environment

    Args:
        env: training environment

    Attributes:
        env (gym3.Env): OpenAI gym training environment
        n_envs (int): Number of vectorized envs
        obs (int): Array of env observation state
        replay_buffer (TYPE): Data collector for saving experience
    """
    def __init__(self, env: gym3.Env, replay_buffer) -> None:
        """Initializes agent class

        Args:
            env (gym3.Env): OpenAI gym training environment
            replay_buffer (TYPE): Data collector for saving experience
        """
        self.env = env
        self.n_envs = self.env.num
        self.replay_buffer = replay_buffer
        self.reset_all()

    def process_obs(self, obs: int) -> torch.Tensor:
        """Converts obs np.array to torch.Tensor for passing through NN

        Args:
            obs (int): Array of env observation state

        Returns:
            torch.Tensor: Torch tensor of observation
        """
        return torch.from_numpy(obs).float().unsqueeze(0)

    def get_action(
        self,
        net: nn.Module,
    ) -> int:
        """
        Using the given network, decide what action to carry out

        Args:
            net (nn.Module): Policy network

        Returns:
            action (int): Action to be carried out
        """
        obs = self.process_obs(self.obs)

        action_logit = net(obs)
        probs = F.softmax(action_logit, dim=-1)
        dist = torch.distributions.Categorical(probs)
        action = dist.sample().squeeze().numpy()
        action = np.expand_dims(action, axis=0) if action.ndim == 0 else action
        return action

    @torch.no_grad()
    def play_step(
        self,
        net: nn.Module,
    ) -> Tuple[float, bool]:
        """
        Carries out a single interaction step between the agent and the
        environment

        Args:
            net (nn.Module): Policy network

        Returns:
            reward (float): Reward received due to taken step
            done (bool): Indicates if a step is terminal
        """
        action = self.get_action(net)

        # do step in the environment
        self.env.act(action)
        reward, new_obs, first = self.env.observe()

        s = dict(
            zip(Experience._fields,
                (self.obs, action, reward, first, new_obs)))
        step = {
            k: {e_k: []
                for e_k in range(self.n_envs)}
            for k in Experience._fields
        }
        step = {k: {e_k: s[k][e_k] for e_k in v} for k, v in step.items()}

        for i in range(self.n_envs):
            for k in Experience._fields:
                self.rollouts[k][i].append(step[k][i])
            if step['first'][i]:
                exp = Experience(*(v[i] for v in self.rollouts.values()))
                self.replay_buffer.append(exp)
                for k in Experience._fields:
                    self.rollouts[k][i] = []

        self.obs = new_obs
        return first

    def reset_all(self):
        self.obs = np.concatenate(
            [e.callmethod("reset") for e in self.env.envs])
        self.rollouts = {i: defaultdict(list) for i in Experience._fields}
        self.rollouts = {
            k: {e_k: []
                for e_k in range(self.n_envs)}
            for k, v in self.rollouts.items()
        }

class GreedyAgent:
    """
    Base off-policy Agent class handling the interaction with the environment

    Args:
        env: training environment

    Attributes:
        env (gym3.Env): OpenAI gym training environment
        n_envs (int): Number of vectorized envs
        replay_buffer (TYPE): Data collector for saving experience
    """
    def __init__(self, env: gym3.Env, replay_buffer, eps_start: float, eps_end: float, eps_frames: int) -> None:
        """Initializes agent class

        Args:
            env (gym3.Env): OpenAI gym training environment
            replay_buffer (TYPE): Data collector for saving experience
        """
        self.env = env
        self.n_envs = self.env.num
        self.epsilon = eps_start
        self.epsilon_start = eps_start
        self.epsilon_end = eps_end
        self.epsilon_frames = eps_frames
        self.step = 0
        self.replay_buffer = replay_buffer
        self.reset_all()

    def update_epsilon(self):
        self.epsilon = max(self.epsilon_end, self.epsilon_start - (self.step + 1) / self.epsilon_frames)

    def process_obs(self, obs: np.ndarray, device: torch.device) -> torch.Tensor:
        """Converts obs np.array to torch.Tensor for passing through NN

        Args:
            obs (np.ndarray): Array of env observation state
            device (torch.device): device used for current obs

        Returns:
            torch.Tensor: Torch tensor of observation
        """
        return torch.from_numpy(obs).float().unsqueeze(0).to(device)

    def get_action(
        self,
        net: nn.Module,
    ) -> int:
        """
        Using the given network, decide what action to carry out

        Args:
            net (nn.Module): Policy network

        Returns:
            action (int): Action to be carried out
        """

        obs = self.process_obs(self.obs, self.get_device(net))

        q_values = net(obs)
        _, actions = torch.max(q_values, dim=1)

        random_idx = np.random.random(self.n_envs) < self.epsilon
        actions[random_idx] = np.random.randint(0, self.env.ac_space.eltype.n, len(random_idx))

        return actions.detach().cpu().numpy()

    @torch.no_grad()
    def play_step(
        self,
        net: nn.Module,
    ) -> Tuple[float, bool]:
        """
        Carries out a single interaction step between the agent and the
        environment

        Args:
            net (nn.Module): Policy network

        Returns:
            reward (float): Reward received due to taken step
            done (bool): Indicates if a step is terminal
        """
        action = self.get_action(net)

        ######## update epsilon

        # do step in the environment
        self.env.act(action)
        reward, new_obs, first = self.env.observe()

        s = dict(
            zip(Experience._fields,
                (self.obs, action, reward, first, new_obs)))
        step = {
            k: {e_k: []
                for e_k in range(self.n_envs)}
            for k in Experience._fields
        }
        step = {k: {e_k: s[k][e_k] for e_k in v} for k, v in step.items()}

        for i in range(self.n_envs):
            for k in Experience._fields:
                self.rollouts[k][i].append(step[k][i])
            if step['first'][i]:
                exp = Experience(*(v[i] for v in self.rollouts.values()))
                self.replay_buffer.append(exp)
                for k in Experience._fields:
                    self.rollouts[k][i] = []

        self.obs = new_obs
        return first

    def reset_all(self):
        self.obs = np.concatenate(
            [e.callmethod("reset") for e in self.env.envs])
        self.rollouts = {i: defaultdict(list) for i in Experience._fields}
        self.rollouts = {
            k: {e_k: []
                for e_k in range(self.n_envs)}
            for k, v in self.rollouts.items()
        }

    def get_device(self, net: nn.Module) -> torch.device:
        return next(net.parameters()).device