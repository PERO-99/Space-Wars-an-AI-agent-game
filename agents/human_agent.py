"""Human-controlled agent.

This agent doesn't decide actions on its own. Instead, the web UI (or any client)
can push actions into its queue over WebSocket, enabling an "AI vs You" mode.

It conforms to the BaseAgent interface and returns structured actions so the
existing decision panels keep working.
"""

from __future__ import annotations

from collections import deque
from typing import Deque, Optional

from agents.base_agent import BaseAgent
from environment.game_state import GameState


class HumanAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="human")
        self._queue: Deque[dict] = deque()
        self.player_name: str = "YOU"

    def reset(self) -> None:
        super().reset()
        self._queue.clear()

    def enqueue_action(self, src: int, dst: int, ships: int, reason: str = "Manual command") -> None:
        self._queue.append({
            "type": "COMMAND",
            "from": int(src),
            "to": int(dst),
            "ships": int(ships),
            "reason": reason,
            "confidence": 1.0,
        })

    def predict(self, state: GameState, player_id: int, observation: dict = None) -> list[dict]:
        """Return all queued actions and clear the queue."""
        actions: list[dict] = []
        while self._queue:
            a = self._queue.popleft()
            # Basic validation (engine will still validate/ignore invalid sends)
            if a["from"] < 0 or a["to"] < 0 or a["ships"] <= 0:
                continue
            actions.append(a)

        self.last_decision = actions
        return actions

    def select_action(self, observation: dict, state: GameState, player_id: int):
        pred = self.predict(state, player_id, observation)
        return [(p["from"], p["to"], p["ships"]) for p in pred]
