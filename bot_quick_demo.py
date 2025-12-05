#!/usr/bin/env python3
"""Quick demo of checkers bot algorithms"""

from src.game import Game
from src.bot import RandomBot, MinimaxBot, AlphaBetaBot
import time


def main():
    print("="*70)
    print("CHECKERS BOT ALGORITHMS - QUICK DEMO")
    print("="*70)

    # Demo: Compare algorithms
    print("\nComparing Minimax vs Alpha-Beta Pruning")
    print("-" * 70)
    print("Both algorithms make the same decisions, but Alpha-Beta is faster!\n")

    game = Game(silent=True)

    # Minimax
    print("Minimax (depth=3)...")
    minimax = MinimaxBot('red', depth=3)
    start = time.time()
    move = minimax.get_move(game)
    minimax_time = time.time() - start
    print(f"  Move: {move}")
    print(f"  Nodes explored: {minimax.nodes_explored:,}")
    print(f"  Time: {minimax_time:.3f}s")

    # Alpha-Beta
    print("\nAlpha-Beta Pruning (depth=3)...")
    game = Game(silent=True)  # Reset
    alphabeta = AlphaBetaBot('red', depth=3)
    start = time.time()
    move = alphabeta.get_move(game)
    alphabeta_time = time.time() - start
    print(f"  Move: {move}")
    print(f"  Nodes explored: {alphabeta.nodes_explored:,}")
    print(f"  Time: {alphabeta_time:.3f}s")

    reduction = (1 - alphabeta.nodes_explored / minimax.nodes_explored) * 100
    speedup = minimax_time / alphabeta_time

    print(f"\nResult:")
    print(f"  Alpha-Beta explored {reduction:.1f}% fewer nodes")
    print(f"  Alpha-Beta was {speedup:.1f}x faster")

    # Quick game
    print("\n" + "="*70)
    print("SAMPLE GAME: Minimax vs Random")
    print("="*70)

    game = Game(silent=True)
    red_bot = MinimaxBot('red', depth=2)
    black_bot = RandomBot('black')

    moves = 0
    max_moves = 50

    while not game.is_over() and moves < max_moves:
        current_bot = red_bot if game.current_turn == 'red' else black_bot
        move = current_bot.get_move(game)

        if move is None:
            break

        game.play_move(move[0], move[1])
        moves += 1

    print(f"\nGame finished in {moves} moves")
    if game.is_over():
        print(f"Winner: {game.winner}")
        if game.winner == 'red':
            print("Minimax (strategic AI) wins!")
        else:
            print("Random bot got lucky!")
    else:
        print("Draw")

    print("\n" + "="*70)
    print("ALGORITHMS EXPLAINED")
    print("="*70)

    print("\n1. RANDOM BOT")
    print("   - Simply picks a random valid move")
    print("   - Fast but no strategy")

    print("\n2. MINIMAX")
    print("   - Looks ahead multiple moves")
    print("   - Assumes both players play optimally")
    print("   - Evaluates positions based on piece count, kings, position")
    print("   - Complexity: O(b^d) where b=branching, d=depth")

    print("\n3. ALPHA-BETA PRUNING")
    print("   - Optimized Minimax")
    print("   - Eliminates branches that won't affect final decision")
    print("   - Same result as Minimax, but much faster")
    print("   - Can search deeper in same time")

    print("\n" + "="*70)
    print("Try the full demo: python bot_demo.py")
    print("Run tests: python -m pytest tests/")
    print("="*70)


if __name__ == "__main__":
    main()