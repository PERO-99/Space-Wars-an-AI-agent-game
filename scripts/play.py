"""
Live Game Viewer — Watch AI agents battle with real-time visualization.

Usage:
    python scripts/play.py                               # Default (greedy vs aggressive)
    python scripts/play.py --p1 defensive --p2 greedy     # Custom agents
    python scripts/play.py --port 9000                     # Custom port
"""

import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.server import VisualizationServer


def main():
    parser = argparse.ArgumentParser(description='Planet Wars Live Viewer')
    
    parser.add_argument('--host', type=str, default='localhost')
    parser.add_argument('--port', type=int, default=8765)
    
    args = parser.parse_args()
    
    print("\n🪐 PLANET WARS — Live Battle Viewer")
    print("="  * 40)
    
    server = VisualizationServer(host=args.host, port=args.port)
    server.start()


if __name__ == '__main__':
    main()
