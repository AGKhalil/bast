import numpy as np
import torch
from torch.utils.data.dataset import IterableDataset
from collections import deque
from collections import namedtuple
from squiRL.common.policies import MLP
import gym
from typing import Tuple

Experience = namedtuple('Experience',
                        ('state', 'action', 'reward', 'done', 'last_state'))


class RolloutCollector:
    """
    Buffer for collecting rollout experiences allowing the agent to learn from
    them

    Args:
        capacity: size of the buffer
    """
    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.replay_buffer = deque(maxlen=self.capacity)

    def __len__(self) -> None:
        return len(self.replay_buffer)

    def append(self, experience: Experience) -> None:
        """
        Add experience to the buffer

        Args:
            experience: tuple (state, action, reward, done, new_state)
        """
        self.replay_buffer.append(experience)

    def sample(self) -> Tuple:
        states, actions, rewards, dones, next_states = zip(
            *[self.replay_buffer[i] for i in range(len(self.replay_buffer))])

        return (np.array(states), np.array(actions),
                np.array(rewards, dtype=np.float32),
                np.array(dones, dtype=np.bool), np.array(next_states))

    def empty_buffer(self):
        self.replay_buffer.clear()


class RLDataset(IterableDataset):
    """
    Iterable Dataset containing the ExperienceBuffer
    which will be updated with new experiences during training

    Args:
        replay_buffer: replay buffer
        sample_size: number of experiences to sample at a time
    """
    def __init__(self, replay_buffer: RolloutCollector, env: gym.Env,
                 net: MLP, agent) -> None:
        self.replay_buffer = replay_buffer
        self.env = env
        self.net = net
        self.agent = agent
        self.holder = torch.tensor([])
        self.device = 'cuda:0'  # need a better way

    def populate(self) -> None:
        """
        Samples an entire episode

        """
        self.replay_buffer.empty_buffer()
        done = False
        while not done:
            reward, done = self.agent.play_step(self.net)

    def __iter__(self):
        for i in range(1):
            self.populate()
            states, actions, rewards, dones, new_states = self.replay_buffer.sample(
            )
            yield (states, actions, rewards, dones, new_states)
