
from collections import Counter
from stockfish import Stockfish
from move_generator import MoveGenerator

stockfish_path = "stockfish_14.1_win_x64_avx2/stockfish_14.1_win_x64_avx2.exe"


class Heuristics:
    ADVANTAGE_THRESHOLD = 0.95
    PIN_THRESHOLD = 0.0
    FORK_THRESHOLD = 0.05
    SACRIFICE_THRESHOLD = 0.0

    def __init__(self, values: dict = None) -> None:
        # Defining initial material value (weights from AlphaZero)
        self.values = {
            'p': 1.00,
            'n': 3.05,
            'b': 3.33,
            'r': 5.63,
            'q': 9.50,
            'k': 0.00  # we don't consider king's value when counting material
        }
        if values:
            self.values = values

        self.map_fen = {alpha: num for alpha, num in zip("abcdefgh", range(8))}

        # List of all constants
        # Through previous literature, updated with AlphaZero weights
        self.pin_constant = 21
        self.fork_constant = 41.52
        self.sacrifice_constant = [9.50, 15.13, 20.76, 24.09, 27.42]
        self.material_disadvantage_constant = 41.52

        self.heuristic_functions = {
            "Material": self.material_disadvantage,
            "Sacrifice": self.sacrifice,
            "Pin": self.pin,
            "Fork": self.fork,
        }

        self.move_generator = MoveGenerator()
        self.stockfish = Stockfish(stockfish_path)
        self.stockfish.set_depth(10)

    def get_piece_pos(self, piece):
        col, row = piece
        row = 8 - int(row)
        col = self.map_fen[col]

        return row, col

    def check_straight_lines(self, board, row, column, friendly_pieces, values):
        # vertical

        pins = []
        the_value = -100
        for target_row in range(row - 1, -1, -1):
            if board[target_row][column] in friendly_pieces:
                break
            if board[target_row][column] == '-':
                continue
            if the_value == -100:
                the_value = values[board[target_row][column].lower()]
            else:
                new_value = values[board[target_row][column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
        the_value = -100
        for target_row in range(row + 1, 8):
            if board[target_row][column] in friendly_pieces:
                break
            if board[target_row][column] == '-':
                continue
            if the_value == -100:
                the_value = values[board[target_row][column].lower()]
            else:
                new_value = values[board[target_row][column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break

        # horizontal
        the_value = -100
        for target_column in range(column - 1, -1, -1):
            if board[row][target_column] in friendly_pieces:
                break
            if board[row][target_column] == '-':
                continue
            if the_value == -100:
                the_value = values[board[row][target_column].lower()]
            else:
                new_value = values[board[row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
        the_value = -100
        for target_column in range(column + 1, 8):
            if board[row][target_column] in friendly_pieces:
                break
            if board[row][target_column] == '-':
                continue
            if the_value == -100:
                the_value = values[board[row][target_column].lower()]
            else:
                new_value = values[board[row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break

        return pins

    def check_diagonal_lines(self, board, row, column, friendly_pieces, values):
        pins = []
        # upper left
        target_row = row - 1
        target_column = column - 1
        the_value = -100
        while target_row >= 0 and target_column >= 0:
            if board[target_row][target_column] in friendly_pieces:
                break
            if board[target_row][target_column] == '-':
                target_row = target_row - 1
                target_column = target_column - 1
                continue
            if the_value == -100:
                the_value = values[board[target_row][target_column].lower()]
            else:
                new_value = values[board[target_row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
            target_row = target_row - 1
            target_column = target_column - 1

        # upper right
        target_row = row - 1
        target_column = column + 1
        the_value = -100
        while target_row >= 0 and target_column <= 7:
            if board[target_row][target_column] in friendly_pieces:
                break
            if board[target_row][target_column] == '-':
                target_row = target_row - 1
                target_column = target_column + 1
                continue
            if the_value == -100:
                the_value = values[board[target_row][target_column].lower()]
            else:
                new_value = values[board[target_row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
            target_row = target_row - 1
            target_column = target_column + 1

        # lower left
        target_row = row + 1
        target_column = column - 1
        the_value = -100
        while target_row <= 7 and target_column >= 0:
            if board[target_row][target_column] in friendly_pieces:
                break
            if board[target_row][target_column] == '-':
                target_row = target_row + 1
                target_column = target_column - 1
                continue
            if the_value == -100:
                the_value = values[board[target_row][target_column].lower()]
            else:
                new_value = values[board[target_row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
            target_row = target_row + 1
            target_column = target_column - 1

        # lower right
        target_row = row + 1
        target_column = column + 1
        the_value = -100
        while target_row <= 7 and target_column <= 7:
            if board[target_row][target_column] in friendly_pieces:
                break
            if board[target_row][target_column] == '-':
                target_row = target_row + 1
                target_column = target_column + 1
                continue
            if the_value == -100:
                the_value = values[board[target_row][target_column].lower()]
            else:
                new_value = values[board[target_row][target_column].lower()]
                if new_value > the_value:
                    pins.append(new_value + the_value)
                    break
            target_row = target_row + 1
            target_column = target_column + 1
        return pins

    def get_pinned_pieces(self, fen_position: str) -> list:
        values = self.values
        values['k'] = 15

        white_pieces = 'RNBQKP'
        black_pieces = 'rnbqkp'

        player = fen_position.split()[1]
        friendly_pieces = black_pieces if player == 'b' else white_pieces
        board_array = MoveGenerator.board_numpy(fen_position)

        pinned_pieces = []
        for row in range(8):
            for column in range(8):
                piece = board_array[row][column]
                if piece in friendly_pieces:
                    the_value = -100
                    found = 0
                    if piece.lower() in ['r', 'q']:
                        straight_pins = self.check_straight_lines(board_array, row, column, friendly_pieces, values)
                        if len(straight_pins) > 0:
                            pinned_pieces.append(max(straight_pins))
                        diagonal_pins = self.check_diagonal_lines(board_array, row, column, friendly_pieces, values)
                        if len(diagonal_pins) > 0:
                            pinned_pieces.append(max(diagonal_pins))

        return pinned_pieces

    def total_material(self, fen_position: str, **args) -> (float, float):
        fen = fen_position.split()[0]
        fen = [piece for piece in fen if piece.isalpha()]
        counter = Counter(fen)

        white_material = 0
        black_material = 0

        for piece, count in counter.items():
            if piece.isupper():
                white_material += count * self.values[piece.lower()]
            else:
                black_material += count * self.values[piece]

        white_material, black_material = round(white_material, 2), round(black_material, 2)
        return white_material, black_material

    def stockfish_evaluation(self, fen_position: str, *args) -> dict:
        self.stockfish.set_fen_position(fen_position)
        return self.stockfish.get_evaluation()

    def material_disadvantage(self, fen_position: str, *args) -> (bool, float):
        white, black = self.total_material(fen_position=fen_position)
        return white * Heuristics.ADVANTAGE_THRESHOLD > black, abs((white - black) / self.material_disadvantage_constant)

    def sacrifice(self, fen_position_initial: str, fen_position_end: str, num_moves: int) -> (bool, float):
        if not fen_position_end:
            return False, 0
        white_initial, black_initial = self.total_material(fen_position=fen_position_initial)
        white_end, black_end = self.total_material(fen_position=fen_position_end)

        sacrifice_value = ((white_initial - white_end) - (black_initial - black_end)) / self.sacrifice_constant[
            num_moves - 1]

        return sacrifice_value > Heuristics.SACRIFICE_THRESHOLD, sacrifice_value

    def pin(self, fen_position: str, *args) -> (bool, float):
        pin_value = 0  # TODO: Calculate the pin value
        values = self.get_pinned_pieces(fen_position)
        if values:
            pin_value = max(pin_value, max(values) / self.pin_constant)

        return pin_value > Heuristics.PIN_THRESHOLD, pin_value

    def fork(self, fen_position: str, *args) -> (bool, float):
        moves = self.move_generator.get_capture_moves(fen_position)
        board_numpy = MoveGenerator.board_numpy(fen_position)

        fork_value = 0  # TODO: Calculate the pin value

        captures = {}
        for move in moves:
            if move[:2] in captures:
                captures[move[:2]].append(move[3:])
            else:
                captures[move[:2]] = [move[3:]]

        for key, value in captures.items():
            row, col = self.get_piece_pos(key)
            key = board_numpy[row][col]

            if len(value) > 1:
                forks = []
                for captured_piece in value:
                    row, col = self.get_piece_pos(captured_piece)
                    piece = board_numpy[row][col]

                    if self.values[piece.lower()] >= self.values[key.lower()]:
                        forks.append(piece)
                if len(forks) > 1:
                    # run fork formula here
                    fork_value += (1 / self.fork_constant) * (
                                sum([self.values[piece.lower()] for piece in forks]) / self.values[key.lower()] + len(
                            forks))

        return fork_value > Heuristics.FORK_THRESHOLD, fork_value

    def get_all_heuristics(self, fen_position_start: str, fen_position_end: str = None, num_moves=None) -> (
    dict, float):
        result = {}
        total = 0
        for name, func in self.heuristic_functions.items():
            flag, val = func(fen_position_start, fen_position_end, num_moves)
            if flag:
                total += val
            result[name] = (flag, val)
        # result["stockfish"] = self.stockfish_evaluation(fen_position_start)
        return result, total

