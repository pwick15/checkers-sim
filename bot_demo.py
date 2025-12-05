#!/usr/bin/env python3
"""
Bot Demo - Showcases different AI algorithms playing checkers

This script demonstrates:
1. Random bot vs Random bot (baseline)
2. Minimax bot vs Random bot
3. Alpha-Beta bot vs Minimax bot
"""

from src.game import Game
from src.bot import RandomBot, MinimaxBot, AlphaBetaBot
import time


def play_game(red_bot, black_bot, verbose=True, max_moves=100):
    """
    Play a game between two bots.

    Args:
        red_bot: Bot playing as red
        black_bot: Bot playing as black
        verbose: Print game progress
        max_moves: Maximum moves before declaring draw

    Returns:
        str: Winner color or 'draw'
    """
    game = Game(silent=not verbose)
    moves = 0

    if verbose:
        print("\nStarting game...")
        print(f"Red: {red_bot.__class__.__name__}")
        print(f"Black: {black_bot.__class__.__name__}")
        print("=" * 50)

    while not game.is_over() and moves < max_moves:
        current_bot = red_bot if game.current_turn == 'red' else black_bot

        if verbose and moves < 10:  # Only print first few moves
            print(f"\nMove {moves + 1} - {game.current_turn}'s turn")

        # Get bot's move
        move = current_bot.get_move(game)

        if move is None:
            # No valid moves
            break

        start_pos, end_pos = move

        # Make the move
        success = game.play_move(start_pos, end_pos)

        if not success:
            if verbose:
                print(f"Invalid move attempted: {start_pos} -> {end_pos}")
            break

        moves += 1

    if game.is_over():
        if verbose:
            print(f"\nGame Over! Winner: {game.winner}")
            print(f"Total moves: {moves}")
        return game.winner
    else:
        if verbose:
            print(f"\nDraw after {moves} moves")
        return 'draw'


def run_tournament(bot1_class, bot2_class, games=5, **bot_kwargs):
    """
    Run a tournament between two bot types.

    Args:
        bot1_class: First bot class
        bot2_class: Second bot class
        games: Number of games to play
        **bot_kwargs: Arguments to pass to bot constructors
    """
    print(f"\n{'='*60}")
    print(f"TOURNAMENT: {bot1_class.__name__} vs {bot2_class.__name__}")
    print(f"{'='*60}")

    bot1_wins = 0
    bot2_wins = 0
    draws = 0
    total_nodes_bot1 = 0
    total_nodes_bot2 = 0

    for i in range(games):
        print(f"\nGame {i + 1}/{games}:")

        # Alternate who plays red
        # Only pass bot_kwargs to bots that accept them (not RandomBot)
        if i % 2 == 0:
            if bot1_class == RandomBot:
                red_bot = bot1_class('red')
            else:
                red_bot = bot1_class('red', **bot_kwargs)

            if bot2_class == RandomBot:
                black_bot = bot2_class('black')
            else:
                black_bot = bot2_class('black', **bot_kwargs)

            bot1_color = 'red'
            bot2_color = 'black'
        else:
            if bot2_class == RandomBot:
                red_bot = bot2_class('red')
            else:
                red_bot = bot2_class('red', **bot_kwargs)

            if bot1_class == RandomBot:
                black_bot = bot1_class('black')
            else:
                black_bot = bot1_class('black', **bot_kwargs)

            bot1_color = 'black'
            bot2_color = 'red'

        winner = play_game(red_bot, black_bot, verbose=False)

        if winner == bot1_color:
            bot1_wins += 1
            print(f"  Winner: {bot1_class.__name__}")
        elif winner == bot2_color:
            bot2_wins += 1
            print(f"  Winner: {bot2_class.__name__}")
        else:
            draws += 1
            print(f"  Draw")

        # Track node exploration if available
        if hasattr(red_bot, 'nodes_explored'):
            if bot1_color == 'red':
                total_nodes_bot1 += red_bot.nodes_explored
                total_nodes_bot2 += black_bot.nodes_explored
            else:
                total_nodes_bot1 += black_bot.nodes_explored
                total_nodes_bot2 += red_bot.nodes_explored

    print(f"\n{'='*60}")
    print("RESULTS:")
    print(f"  {bot1_class.__name__}: {bot1_wins} wins")
    print(f"  {bot2_class.__name__}: {bot2_wins} wins")
    print(f"  Draws: {draws}")

    if total_nodes_bot1 > 0 or total_nodes_bot2 > 0:
        print(f"\nNODES EXPLORED (average per game):")
        print(f"  {bot1_class.__name__}: {total_nodes_bot1 // games:,}")
        print(f"  {bot2_class.__name__}: {total_nodes_bot2 // games:,}")

    print(f"{'='*60}\n")


def educational_demo():
    """
    Educational demo explaining the algorithms.
    """
    print("\n" + "="*70)
    print("CHECKERS BOT ALGORITHMS - EDUCATIONAL DEMO")
    print("="*70)

    print("\n1. RANDOM BOT")
    print("-" * 70)
    print("The simplest strategy: picks a random valid move.")
    print("- Pros: Fast, unpredictable")
    print("- Cons: No strategic thinking, plays poorly")

    print("\n2. MINIMAX ALGORITHM")
    print("-" * 70)
    print("Classic game tree search algorithm.")
    print("How it works:")
    print("  1. Explores all possible moves to a certain depth")
    print("  2. Assumes both players play optimally")
    print("  3. At each level, alternates between maximizing and minimizing")
    print("  4. Uses an evaluation function to score positions")
    print("\nEvaluation considers:")
    print("  - Number of pieces (more is better)")
    print("  - King pieces (worth more)")
    print("  - Position on board (advancing is good)")
    print("\n- Pros: Plays strategically, finds good moves")
    print("- Cons: Slow for deep searches (exponential complexity)")

    print("\n3. ALPHA-BETA PRUNING")
    print("-" * 70)
    print("Optimization of Minimax that eliminates unnecessary branches.")
    print("How it works:")
    print("  - Keeps track of 'alpha' (best maximizing score)")
    print("  - Keeps track of 'beta' (best minimizing score)")
    print("  - Prunes branches where beta <= alpha")
    print("  - Gives EXACT same result as Minimax, but faster!")
    print("\n- Pros: Much faster than Minimax, same quality moves")
    print("- Cons: Still limited by computational resources")

    print("\n" + "="*70)
    print("DEMONSTRATION GAMES")
    print("="*70)

    # Demo 1: Compare node exploration
    print("\nDemo 1: Comparing Algorithm Efficiency")
    print("-" * 70)
    game = Game()

    minimax = MinimaxBot('red', depth=3)
    alphabeta = AlphaBetaBot('red', depth=3)

    print("Finding best move from starting position (depth=3)...\n")

    start = time.time()
    minimax.get_move(game)
    minimax_time = time.time() - start

    game = Game()  # Reset
    start = time.time()
    alphabeta.get_move(game)
    alphabeta_time = time.time() - start

    print(f"Minimax:")
    print(f"  Nodes explored: {minimax.nodes_explored:,}")
    print(f"  Time: {minimax_time:.3f}s")

    print(f"\nAlpha-Beta Pruning:")
    print(f"  Nodes explored: {alphabeta.nodes_explored:,}")
    print(f"  Time: {alphabeta_time:.3f}s")

    reduction = (1 - alphabeta.nodes_explored / minimax.nodes_explored) * 100
    print(f"\nAlpha-Beta explored {reduction:.1f}% fewer nodes!")

    # Demo 2: Quick sample game
    print("\n\nDemo 2: Sample Game (Minimax vs Random)")
    print("-" * 70)
    red_bot = MinimaxBot('red', depth=3)
    black_bot = RandomBot('black')
    play_game(red_bot, black_bot, verbose=True, max_moves=50)


def main():
    """Main demo function."""
    educational_demo()

    # Run tournaments
    print("\n\nRUNNING TOURNAMENTS...")
    print("(This may take a minute...)\n")

    # Tournament 1: Random vs Random (baseline)
    run_tournament(RandomBot, RandomBot, games=3)

    # Tournament 2: Minimax vs Random
    run_tournament(MinimaxBot, RandomBot, games=3, depth=3)

    # Tournament 3: Alpha-Beta vs Minimax
    run_tournament(AlphaBetaBot, MinimaxBot, games=3, depth=3)

    print("\nDEMO COMPLETE!")
    print("\nKey Takeaways:")
    print("1. Random bot is fast but plays poorly")
    print("2. Minimax plays strategically by looking ahead")
    print("3. Alpha-Beta gives same results as Minimax but much faster")
    print("4. Higher depth = smarter play but slower computation")
    print("\nTry adjusting the depth parameter to see the trade-off between")
    print("playing strength and computation time!")


if __name__ == "__main__":
    main()
