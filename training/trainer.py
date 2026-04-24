"""
PPO Trainer — Main training loop with self-play and curriculum learning.

Implements the complete training pipeline:
1. Collect rollouts from parallel environments
2. Compute GAE advantages
3. PPO clipped objective optimization
4. Periodic checkpointing and evaluation
5. Curriculum stage management
6. Self-play opponent pool updates
"""

from __future__ import annotations
import os
import time
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Optional

from agents.rl.ppo_agent import PPOAgent
from training.experience_buffer import ExperienceBuffer
from training.parallel_envs import VectorizedEnvs
from training.self_play import SelfPlayManager
from training.curriculum import CurriculumScheduler
from training.logger import TrainingLogger
from environment.gym_env import PlanetWarsEnv


class PPOTrainer:
    """
    Complete PPO training pipeline with:
    - Vectorized environment data collection
    - GAE advantage estimation
    - Clipped PPO objective
    - Self-play opponent pool
    - Curriculum learning
    - TensorBoard logging
    - Model checkpointing
    """
    
    def __init__(
        self,
        # PPO hyperparameters
        learning_rate: float = 3e-4,
        gamma: float = 0.99,
        gae_lambda: float = 0.95,
        clip_epsilon: float = 0.2,
        value_loss_coeff: float = 0.5,
        entropy_coeff: float = 0.01,
        max_grad_norm: float = 0.5,
        num_epochs: int = 4,
        batch_size: int = 64,
        rollout_length: int = 128,
        # Training settings
        num_parallel_envs: int = 8,
        total_iterations: int = 1000,
        checkpoint_interval: int = 25,
        log_interval: int = 5,
        snapshot_interval: int = 50,
        # Environment settings
        map_name: str = 'duel_medium',
        use_generated_maps: bool = True,
        max_turns: int = 200,
        # Agent settings
        max_planets: int = 30,
        max_fleets: int = 50,
        embed_dim: int = 64,
        hidden_dim: int = 128,
        # Directories
        checkpoint_dir: str = 'checkpoints',
        log_dir: str = 'logs',
        experiment_name: str = None,
        # Device
        device: str = 'auto',
    ):
        # Save all hyperparameters
        self.lr = learning_rate
        self.gamma = gamma
        self.gae_lambda = gae_lambda
        self.clip_epsilon = clip_epsilon
        self.value_loss_coeff = value_loss_coeff
        self.entropy_coeff = entropy_coeff
        self.max_grad_norm = max_grad_norm
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.rollout_length = rollout_length
        self.num_parallel_envs = num_parallel_envs
        self.total_iterations = total_iterations
        self.checkpoint_interval = checkpoint_interval
        self.log_interval = log_interval
        self.snapshot_interval = snapshot_interval
        self.checkpoint_dir = checkpoint_dir
        
        os.makedirs(checkpoint_dir, exist_ok=True)
        
        # Initialize agent
        self.agent = PPOAgent(
            max_planets=max_planets,
            max_fleets=max_fleets,
            embed_dim=embed_dim,
            hidden_dim=hidden_dim,
            device=device,
        )
        
        # Optimizer
        self.optimizer = optim.Adam(
            self.agent.network.parameters(),
            lr=learning_rate,
            eps=1e-5,
        )
        
        # Curriculum and self-play
        self.curriculum = CurriculumScheduler()
        self.self_play = SelfPlayManager(
            checkpoint_dir=os.path.join(checkpoint_dir, 'opponents'))
        
        # Initial opponent
        initial_opponent = self.curriculum.get_opponent()
        
        # Vectorized environments
        self.vec_envs = VectorizedEnvs(
            num_envs=num_parallel_envs,
            opponent=initial_opponent,
            map_name=map_name,
            use_generated_maps=use_generated_maps,
            max_turns=max_turns,
            max_planets=max_planets,
            max_fleets=max_fleets,
        )
        
        # Experience buffer
        obs_dim = self.vec_envs.obs_dim
        action_mask_dim = self.vec_envs.action_dim
        
        self.buffer = ExperienceBuffer(
            buffer_size=rollout_length * num_parallel_envs,
            obs_dim=obs_dim,
            action_mask_dim=action_mask_dim,
            gamma=gamma,
            gae_lambda=gae_lambda,
        )
        
        # Logger
        if experiment_name is None:
            experiment_name = f"ppo_{int(time.time())}"
        self.logger = TrainingLogger(log_dir=log_dir, experiment_name=experiment_name)
        
        # Training stats
        self.total_steps = 0
        self.total_episodes = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
    
    def train(self) -> dict:
        """
        Run the full training loop.
        
        Returns:
            Training statistics.
        """
        self.logger.print("=" * 60)
        self.logger.print("  Planet Wars PPO Training")
        self.logger.print(f"  Device: {self.agent.device}")
        self.logger.print(f"  Total iterations: {self.total_iterations}")
        self.logger.print(f"  Parallel envs: {self.num_parallel_envs}")
        self.logger.print(f"  Rollout length: {self.rollout_length}")
        self.logger.print("=" * 60)
        
        start_time = time.time()
        
        # Initial reset
        observations, infos = self.vec_envs.reset()
        action_masks = self.vec_envs.get_action_masks(infos)
        
        for iteration in range(1, self.total_iterations + 1):
            iter_start = time.time()
            self.agent.set_train_mode()
            
            # --- Collect rollout ---
            self.buffer.reset()
            episode_rewards = []
            episode_lengths = []
            current_ep_rewards = [0.0] * self.num_parallel_envs
            current_ep_lengths = [0] * self.num_parallel_envs
            
            for step in range(self.rollout_length):
                # Select actions for all envs
                actions = []
                log_probs = []
                values = []
                
                for i in range(self.num_parallel_envs):
                    action, log_prob, value, _ = self.agent.select_action_for_training(
                        observations[i], action_masks[i])
                    actions.append(action)
                    log_probs.append(log_prob)
                    values.append(value)
                
                # Step all envs
                next_observations, rewards, terminateds, truncateds, next_infos = \
                    self.vec_envs.step(actions)
                next_action_masks = self.vec_envs.get_action_masks(next_infos)
                
                # Store transitions
                for i in range(self.num_parallel_envs):
                    self.buffer.add(
                        obs=observations[i],
                        action=actions[i],
                        reward=rewards[i],
                        value=values[i],
                        log_prob=log_probs[i],
                        done=terminateds[i] or truncateds[i],
                        action_mask=action_masks[i],
                    )
                    
                    current_ep_rewards[i] += rewards[i]
                    current_ep_lengths[i] += 1
                    
                    # Track episode completion
                    if terminateds[i] or truncateds[i]:
                        episode_rewards.append(current_ep_rewards[i])
                        episode_lengths.append(current_ep_lengths[i])
                        current_ep_rewards[i] = 0.0
                        current_ep_lengths[i] = 0
                        self.total_episodes += 1
                        
                        # Track wins/losses
                        winner = next_infos[i].get('winner')
                        if winner == 1:
                            self.wins += 1
                            self.curriculum.record_result(True)
                        elif winner == 0:
                            self.draws += 1
                            self.curriculum.record_result(False)
                        else:
                            self.losses += 1
                            self.curriculum.record_result(False)
                
                observations = next_observations
                action_masks = next_action_masks
                self.total_steps += self.num_parallel_envs
            
            # Compute last values for GAE
            last_values = []
            for i in range(self.num_parallel_envs):
                v = self.agent.get_value(observations[i], action_masks[i])
                last_values.append(v)
            
            avg_last_value = np.mean(last_values)
            self.buffer.compute_gae(avg_last_value)
            
            # --- PPO Update ---
            update_stats = self._ppo_update()
            
            # --- Curriculum check ---
            advanced = self.curriculum.check_and_advance()
            if advanced:
                self.logger.print(
                    f"\n🎓 CURRICULUM ADVANCE: {self.curriculum.stage_name}")
                
                if self.curriculum.is_self_play:
                    # Switch to self-play
                    opponent = self.self_play.sample_opponent()
                    self.vec_envs.set_opponent(opponent)
                else:
                    opponent = self.curriculum.get_opponent()
                    self.vec_envs.set_opponent(opponent)
            
            # Self-play: update opponent periodically
            if self.curriculum.is_self_play and iteration % self.snapshot_interval == 0:
                self.self_play.add_snapshot(self.agent)
                opponent = self.self_play.sample_opponent()
                self.vec_envs.set_opponent(opponent)
            
            # --- Logging ---
            if iteration % self.log_interval == 0:
                iter_time = time.time() - iter_start
                fps = (self.rollout_length * self.num_parallel_envs) / iter_time
                
                avg_reward = np.mean(episode_rewards) if episode_rewards else 0.0
                avg_length = np.mean(episode_lengths) if episode_lengths else 0.0
                curriculum_stats = self.curriculum.get_stats()
                
                log_data = {
                    'iteration': iteration,
                    'total_steps': self.total_steps,
                    'total_episodes': self.total_episodes,
                    'avg_reward': float(avg_reward),
                    'avg_episode_length': float(avg_length),
                    'wins': self.wins,
                    'losses': self.losses,
                    'draws': self.draws,
                    'win_rate': curriculum_stats['win_rate'],
                    'fps': fps,
                    'curriculum_stage': curriculum_stats['current_stage'],
                    **update_stats,
                }
                
                self.logger.log_dict(log_data, step=iteration)
                
                self.logger.print(
                    f"[Iter {iteration:4d}] "
                    f"reward={avg_reward:+.2f} | "
                    f"WR={curriculum_stats['win_rate']:.1%} | "
                    f"stage={curriculum_stats['current_stage']} | "
                    f"loss={update_stats['total_loss']:.4f} | "
                    f"fps={fps:.0f}"
                )
            
            # --- Checkpoint ---
            if iteration % self.checkpoint_interval == 0:
                self.agent.version = iteration
                ckpt_path = os.path.join(
                    self.checkpoint_dir, f'agent_iter_{iteration}.pt')
                self.agent.save(ckpt_path)
                self.logger.print(f"  💾 Checkpoint saved: {ckpt_path}")
        
        # Final save
        final_path = os.path.join(self.checkpoint_dir, 'agent_final.pt')
        self.agent.save(final_path)
        
        total_time = time.time() - start_time
        self.logger.print(f"\n✅ Training complete in {total_time:.1f}s")
        self.logger.print(f"   Final win rate: {self.curriculum.get_stats()['win_rate']:.1%}")
        self.logger.close()
        
        return {
            'total_steps': self.total_steps,
            'total_episodes': self.total_episodes,
            'wins': self.wins,
            'losses': self.losses,
            'training_time': total_time,
        }
    
    def _ppo_update(self) -> dict:
        """
        Perform PPO clipped objective optimization.
        
        Returns:
            Dict of loss statistics.
        """
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        total_loss_sum = 0.0
        num_updates = 0
        
        for epoch in range(self.num_epochs):
            for batch in self.buffer.get_batches(self.batch_size, self.agent.device):
                obs = batch['observations']
                actions = batch['actions']
                old_log_probs = batch['old_log_probs']
                advantages = batch['advantages']
                returns = batch['returns']
                masks = batch['action_masks']
                
                # Get current policy outputs
                _, new_log_probs, entropy, values = \
                    self.agent.network.get_action_and_value(obs, masks, actions)
                
                # PPO clipped objective
                ratio = torch.exp(new_log_probs - old_log_probs)
                surr1 = ratio * advantages
                surr2 = torch.clamp(ratio, 1 - self.clip_epsilon,
                                    1 + self.clip_epsilon) * advantages
                policy_loss = -torch.min(surr1, surr2).mean()
                
                # Value loss (clipped)
                value_loss = nn.functional.mse_loss(values, returns)
                
                # Entropy bonus
                entropy_loss = -entropy.mean()
                
                # Total loss
                loss = (policy_loss
                        + self.value_loss_coeff * value_loss
                        + self.entropy_coeff * entropy_loss)
                
                # Optimize
                self.optimizer.zero_grad()
                loss.backward()
                nn.utils.clip_grad_norm_(
                    self.agent.network.parameters(), self.max_grad_norm)
                self.optimizer.step()
                
                total_policy_loss += policy_loss.item()
                total_value_loss += value_loss.item()
                total_entropy_loss += entropy_loss.item()
                total_loss_sum += loss.item()
                num_updates += 1
        
        return {
            'policy_loss': total_policy_loss / max(num_updates, 1),
            'value_loss': total_value_loss / max(num_updates, 1),
            'entropy_loss': total_entropy_loss / max(num_updates, 1),
            'total_loss': total_loss_sum / max(num_updates, 1),
            'num_updates': num_updates,
        }
