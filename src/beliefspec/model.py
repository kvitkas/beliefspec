"""Matched recurrent models. No evaluator metadata is accepted here."""

from dataclasses import dataclass

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

N_OBJECTS = 11
N_ACTIONS = 7


@dataclass
class Batch:
    images: torch.Tensor
    directions: torch.Tensor
    prev_actions: torch.Tensor
    stages: torch.Tensor
    actions: torch.Tensor
    lengths: torch.Tensor
    labels: torch.Tensor


def collate(episodes):
    """Pad at right; labels originate in allowed observed history."""
    n, max_t = len(episodes), max(len(e.images) for e in episodes)
    images = np.zeros((n, max_t, 7, 7), dtype=np.int64)
    directions = np.zeros((n, max_t), dtype=np.int64)
    previous = np.full((n, max_t), 7, dtype=np.int64)
    stages = np.ones((n, max_t), dtype=np.int64)
    actions = np.zeros((n, max_t), dtype=np.int64)
    lengths, labels = [], []
    for i, episode in enumerate(episodes):
        length = len(episode.images)
        images[i, :length] = episode.images
        directions[i, :length] = episode.directions
        previous[i, :length] = episode.prev_actions
        stages[i, :length] = episode.stages
        actions[i, : length - 1] = episode.actions
        lengths.append(length)
        labels.append(episode.observed_clue)
    return Batch(*[torch.as_tensor(x, dtype=torch.long) for x in
                   (images, directions, previous, stages, actions, lengths, labels)])


class MemoryModel(nn.Module):
    def __init__(self, encoder_size=48, hidden_size=32):
        super().__init__()
        self.encoder_size = encoder_size
        self.hidden_size = hidden_size
        self.encoder = nn.Sequential(nn.Linear(49 * N_OBJECTS + 4 + 8 + 3, encoder_size),
                                     nn.Tanh())
        self.gru = nn.GRU(encoder_size, hidden_size, batch_first=True)
        self.readout = nn.Linear(hidden_size, 3)
        self.predictor = nn.Linear(hidden_size + N_ACTIONS, 49 * N_OBJECTS)

    def features(self, batch):
        return torch.cat((F.one_hot(batch.images, N_OBJECTS).flatten(2),
                          F.one_hot(batch.directions, 4),
                          F.one_hot(batch.prev_actions, 8),
                          F.one_hot(batch.stages, 3)), dim=-1).float()

    def forward(self, batch, retain_input_grad=False):
        features = self.features(batch)
        if retain_input_grad:
            features.requires_grad_(True)
        encoded = self.encoder(features)
        # Initial state is freshly zeroed by GRU on every call. Padding is causal
        # and cannot change an earlier valid state; gather each true final step.
        states, _ = self.gru(encoded)
        final = states[torch.arange(len(states)), batch.lengths - 1]
        task_logits = self.readout(final)
        action_features = F.one_hot(batch.actions, N_ACTIONS).float()
        predictions = self.predictor(torch.cat((states, action_features), dim=-1))
        predictions = predictions.reshape(*states.shape[:2], 7, 7, N_OBJECTS)
        return {"logits": task_logits, "prediction_logits": predictions,
                "states": states, "features": features}

    def counts(self):
        prediction = sum(p.numel() for p in self.predictor.parameters())
        total = sum(p.numel() for p in self.parameters())
        return {"allocated": total, "shared": total - prediction, "prediction_head": prediction}


def losses(output, batch):
    task = F.cross_entropy(output["logits"], batch.labels)
    # State/action at t predicts view at t+1, excluding padded transitions.
    logits = output["prediction_logits"][:, :-1]
    targets = batch.images[:, 1:]
    mask = torch.arange(targets.shape[1])[None, :] < (batch.lengths - 1)[:, None]
    cell_loss = F.cross_entropy(logits.reshape(-1, N_OBJECTS), targets.reshape(-1),
                                reduction="none").reshape(targets.shape)
    prediction = cell_loss[mask].mean()
    return task, prediction


def clue_to_choice(probabilities, top_clue):
    """Unknown mass is split equally; exact ties choose top. No hidden truth."""
    p = np.asarray(probabilities, dtype=np.float64)
    if p.shape != (3,) or not np.isclose(p.sum(), 1) or np.any(p < 0):
        raise ValueError("Expected normalized [key, ball, unknown] probabilities")
    p_top = float(p[top_clue] + 0.5 * p[2])
    return p_top >= 0.5


def decision_from_memory(memory_record, top_clue):
    """Controller contract: only clue probabilities affect the final action.

    Optional nuisance notes are deliberately ignored; interventions can change
    those notes to audit the controller boundary without editing hidden states.
    """
    return clue_to_choice(memory_record["clue_probabilities"], top_clue)


def baseline_probabilities(episode, method, window=32):
    """Only visible object IDs and public phase are inspected."""
    if method == "current":
        indices = [len(episode.images) - 1]
    elif method == "recent":
        indices = range(max(0, len(episode.images) - window), len(episode.images))
    elif method in ("structured", "episodic"):
        indices = range(len(episode.images))
    else:
        raise ValueError(method)
    # Structured facts and episodic-frame retrieval use the same parser, but
    # store different material. Their equality on this one-fact task is expected.
    fact = 2
    records = []
    for t in indices:
        if episode.stages[t] != 0:
            continue
        image = episode.images[t]
        seen = [label for obj_id, label in ((5, 0), (6, 1)) if np.any(image == obj_id)]
        if len(seen) == 1:
            if method == "episodic":
                records.append(image.copy())
            else:
                fact = seen[0]
    if method == "episodic" and records:
        # Retrieve latest frame matching the explicit clue-phase query.
        retrieved = records[-1]
        fact = 0 if np.any(retrieved == 5) else 1
    return np.eye(3)[fact]
