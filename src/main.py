from .game import Game

def parse_input(input_str):
    """
    Parses user input like "2,1 3,2" into start and end coordinates.
    """
    try:
        parts = input_str.split()
        if len(parts) != 2:
            return None, None

        start_str, end_str = parts[0], parts[1] 
        
        start_row, start_col = map(int, start_str.split(','))
        end_row, end_col = map(int, end_str.split(','))

        return (start_row, start_col), (end_row, end_col)
    except (ValueError, IndexError):
        return None, None


def main():
    """
    The main game loop for the checkers simulator.
    """
    game = Game()
    print("--- Welcome to Terminal Checkers! ---")
    print("Move format: 'row,col row,col'. For example: '5,0 4,1'")

    while not game.is_over():
        print("\n" + str(game.board))
        print(f"Current turn: {game.current_turn.capitalize()}")

        move_input = input("Enter your move: ")
        
        if move_input.lower() == 'exit':
            print("Thanks for playing!")
            break

        start_pos, end_pos = parse_input(move_input)

        if start_pos is None or end_pos is None:
            print("Invalid input format. Please use 'row,col row,col'.")
            continue

        if not game.play_move(start_pos, end_pos):
            print("Move failed. Please try again.")

    if game.winner:
        print("\n--- Game Over ---")
        print(f"The winner is {game.winner.capitalize()}!")
        print(str(game.board))


if __name__ == "__main__":
    main()
