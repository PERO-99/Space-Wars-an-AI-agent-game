"""
TensorBoard and File Logger for training.
"""

from __future__ import annotations
import os
import json
import time
from typing import Optional


class TrainingLogger:
    """Unified logging to TensorBoard, file, and console."""
    
    def __init__(self, log_dir: str = 'logs', experiment_name: str = None):
        if experiment_name is None:
            experiment_name = f"run_{int(time.time())}"
        
        self.log_dir = os.path.join(log_dir, experiment_name)
        os.makedirs(self.log_dir, exist_ok=True)
        
        # TensorBoard
        self.tb_writer = None
        try:
            from torch.utils.tensorboard import SummaryWriter
            self.tb_writer = SummaryWriter(self.log_dir)
        except ImportError:
            print("[Logger] TensorBoard not available, using file logging only.")
        
        # File log
        self.log_file = os.path.join(self.log_dir, 'training_log.jsonl')
        self.csv_file = os.path.join(self.log_dir, 'metrics.csv')
        self._csv_initialized = False
        
        self.step = 0
    
    def log_scalar(self, tag: str, value: float, step: int = None):
        """Log a scalar value."""
        if step is None:
            step = self.step
        
        if self.tb_writer:
            self.tb_writer.add_scalar(tag, value, step)
    
    def log_scalars(self, main_tag: str, tag_scalar_dict: dict, step: int = None):
        """Log multiple scalars under the same main tag."""
        if step is None:
            step = self.step
        
        if self.tb_writer:
            self.tb_writer.add_scalars(main_tag, tag_scalar_dict, step)
    
    def log_dict(self, data: dict, step: int = None):
        """Log a dictionary to file and TensorBoard."""
        if step is None:
            step = self.step
        
        data['step'] = step
        data['timestamp'] = time.time()
        
        # Write to JSONL
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(data) + '\n')
        
        # Write scalars to TensorBoard
        if self.tb_writer:
            for key, value in data.items():
                if isinstance(value, (int, float)) and key not in ('step', 'timestamp'):
                    self.tb_writer.add_scalar(key, value, step)
    
    def log_csv(self, data: dict, step: int = None):
        """Log to CSV file."""
        if step is None:
            step = self.step
        
        data['step'] = step
        
        if not self._csv_initialized:
            with open(self.csv_file, 'w') as f:
                f.write(','.join(data.keys()) + '\n')
            self._csv_initialized = True
        
        with open(self.csv_file, 'a') as f:
            f.write(','.join(str(v) for v in data.values()) + '\n')
    
    def log_text(self, tag: str, text: str, step: int = None):
        """Log text."""
        if step is None:
            step = self.step
        
        if self.tb_writer:
            self.tb_writer.add_text(tag, text, step)
    
    def print(self, msg: str):
        """Print to console and log."""
        print(msg)
        with open(os.path.join(self.log_dir, 'console.log'), 'a') as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    
    def increment_step(self):
        self.step += 1
    
    def close(self):
        if self.tb_writer:
            self.tb_writer.close()
