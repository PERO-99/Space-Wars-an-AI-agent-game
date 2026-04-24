"""
Game Replay Recorder and Player.

Records game states to JSON for replay. Supports playback
at configurable speed.
"""

from __future__ import annotations
import json
import os
from typing import Optional
from environment.game_state import GameState


class ReplayRecorder:
    """Records game states frame-by-frame for replay."""
    
    def __init__(self):
        self.frames: list[dict] = []
        self.metadata: dict = {}
    
    def start(self, metadata: dict = None):
        """Start a new recording."""
        self.frames = []
        self.metadata = metadata or {}
    
    def record_frame(self, state: GameState):
        """Record a single frame (game state)."""
        self.frames.append(state.to_dict())
    
    def save(self, filepath: str):
        """Save recording to JSON file."""
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)
        data = {
            'metadata': self.metadata,
            'num_frames': len(self.frames),
            'frames': self.frames,
        }
        with open(filepath, 'w') as f:
            json.dump(data, f)
    
    @staticmethod
    def load(filepath: str) -> dict:
        """Load a replay from file."""
        with open(filepath, 'r') as f:
            return json.load(f)


class ReplayPlayer:
    """Plays back recorded games frame by frame."""
    
    def __init__(self, replay_data: dict):
        self.frames = replay_data['frames']
        self.metadata = replay_data.get('metadata', {})
        self.current_frame = 0
        self.total_frames = len(self.frames)
    
    def get_frame(self, index: int = None) -> Optional[dict]:
        """Get a specific frame or current frame."""
        idx = index if index is not None else self.current_frame
        if 0 <= idx < self.total_frames:
            return self.frames[idx]
        return None
    
    def next_frame(self) -> Optional[dict]:
        """Advance and return the next frame."""
        if self.current_frame < self.total_frames:
            frame = self.frames[self.current_frame]
            self.current_frame += 1
            return frame
        return None
    
    def reset(self):
        self.current_frame = 0
    
    @property
    def is_finished(self) -> bool:
        return self.current_frame >= self.total_frames
