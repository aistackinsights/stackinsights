# meta_agent.py — Meta-learning agent sketch using MAML-style inner loop
# Article: https://aistackinsights.ai/blog/arc-agi-3-what-1-percent-score-reveals-about-intelligence
import torch, torch.nn as nn
from copy import deepcopy

class AdaptiveAgent(nn.Module):
    def __init__(self, obs_dim: int, action_dim: int, hidden: int = 128):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(obs_dim, hidden), nn.ReLU(),
            nn.Linear(hidden, hidden), nn.ReLU(),
        )
        self.belief_gru = nn.GRUCell(hidden, hidden)
        self.policy_head = nn.Linear(hidden, action_dim)
        self.value_head = nn.Linear(hidden, 1)
        self.belief_state = None

    def reset(self):
        self.belief_state = torch.zeros(1, 128)

    def forward(self, obs: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        z = self.encoder(obs)
        self.belief_state = self.belief_gru(z, self.belief_state)
        return self.policy_head(self.belief_state), self.value_head(self.belief_state)

    def adapt(self, support_trajectory: list, lr: float = 0.01) -> "AdaptiveAgent":
        adapted = deepcopy(self)
        optimizer = torch.optim.SGD(adapted.parameters(), lr=lr)
        for obs, action, reward in support_trajectory:
            optimizer.zero_grad()
            logits, _ = adapted(obs)
            loss = -reward * torch.log_softmax(logits, dim=-1)[0, action]
            loss.backward()
            optimizer.step()
        return adapted
