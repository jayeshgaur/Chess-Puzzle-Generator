
import chess
from numpy import ndarray
import numpy as np

stockfish_path = "stockfish_14.1_win_x64_avx2/stockfish_14.1_win_x64_avx2.exe"


def square(file_index: int, rank_index: int):
    """ Gets a square number by file and rank index """
    return rank_index * 8 + file_index


class ChessBoard(chess.Board):
    def find_move(self, from_square, to_square, promotion=None):
        """ Overridden to suppress move validation """
        return self._from_chess960(self.chess960, from_square, to_square, promotion)


class LegalMoves(chess.LegalMoveGenerator):
    """ Add a new method to existing class to get desired format of moves """
    def to_array(self):
        return [self.board.lan(move) for move in self]


def uci(move):
    move = move.replace("+", "")
    move = move.replace("#", "")
    return move[-5:].replace("-", "")


def inverse(move):
    return move[2:] + move[:2]


def flip_move(position):
    arr = position.split()
    arr[1] = "b" if arr[1] == "w" else "w"
    return " ".join(arr)


class MoveGenerator:
    """
        Previous moves list:
            1. All possible legal (non-pawn) moves at a given position (Breaks down if opponent is in check)
            2. Pawn Moves (back + uncapture)
            3. En Passant (MAYBE we can skip this)
            4. All possible legal moves + uncapture the moves
            5. Un-Castle (not a priority)
    """

    def __init__(self) -> None:
        self.mapper = np.linspace(1, 64, num=64, dtype=int).reshape((8, 8))
        self.map_fen = {alpha: num for alpha, num in zip("abcdefgh", range(8))}

    @staticmethod
    def board_numpy(board) -> ndarray:
        """ Return 2d array for the board position """
        board = board.split()[0].split("/")

        arr = list()

        for row in board:
            res = ""
            for val in row:
                if val.isnumeric():
                    res += int(val) * "-"
                else:
                    res += val
            arr.append(list(res))

        return np.array(arr)

    def index_to_fen(self, index: int) -> str:
        """ Convert 64-value index to board position """
        x, y = 8 - ((index - 1) // 8), (index - 1) % 8
        y = "abcdefgh"[y]

        return y + str(x)

    def get_legal_moves(self, fen_pos: str) -> list:
        board = ChessBoard(fen_pos)
        legal = LegalMoves(board).to_array()
        return [uci(x) for x in legal if not x.islower() and "x" not in x]

    def get_capture_moves(self, fen_pos: str) -> list:
        # TODO: Replace with all moves
        moves = self.get_legal_moves(fen_pos)
        moves = [move for move in moves if "x" in move]
        return moves

    def get_pawn_moves(self, fen_pos: str) -> dict:
        """
            Returns a tuple of (legal_moves, uncapture_moves) for all pawns of player in the given board
            legal_moves: All non-capture moves from board (NOTE: does not validate for discover check)
            uncapture_moves: Possible uncapture moves for all pawns (does not validate anything)
                                -> Requires post-process for which piece to be uncaptured
        """
        player = fen_pos.split()[1]
        fen_pos = MoveGenerator.board_numpy(fen_pos)

        possible_moves, uncapture_moves = [], []

        available_pieces = list(zip(*np.where(fen_pos == 'P'))) if player == "w" \
            else list(zip(*np.where(fen_pos == 'p')))

        updates = {
            "w": {
                "legal": lambda x: x < 6,
                "double_move": lambda x: x == 4,
                "update_one": 8,
                "update_two": 16,
                "capture_left": 7,
                "capture_right": 9,
            },

            "b": {
                "legal": lambda x: x > 1,
                "double_move": lambda x: x == 3,
                "update_one": -8,
                "update_two": -16,
                "capture_left": -9,
                "capture_right": -7,
            }
        }

        for piece in available_pieces:
            if updates[player]["legal"](piece[0]):
                mapper_number = self.mapper[piece[0]][piece[1]]
                possible_moves.append((mapper_number, (mapper_number + updates[player]["update_one"])))
                if updates[player]["double_move"](piece[0]):
                    possible_moves.append((mapper_number, (mapper_number + updates[player]["update_two"])))
                uncapture = [(mapper_number, mapper_number + updates[player]["capture_left"]),
                             (mapper_number, mapper_number + updates[player]["capture_right"])]
                uncapture_moves.extend(uncapture)

        legal_pawn_moves = [
            self.index_to_fen(initial) + self.index_to_fen(end)
            for initial, end in possible_moves
            if fen_pos[np.where(self.mapper == end)] == '-'
        ]

        moves_to_remove = []
        # Illegal pawn uncapture (when space is not empty)
        for move in uncapture_moves:
            row, column = np.where(self.mapper == move[1])
            row, column = row[0], column[0]
            if fen_pos[row][column] != '-':
                moves_to_remove.append(move)

        uncapture_moves = [i for i in uncapture_moves if i not in moves_to_remove]

        uncapture_pawn_moves = [self.index_to_fen(initial) + self.index_to_fen(end) for initial, end in uncapture_moves]

        for move in uncapture_pawn_moves:
            move1 = int(move[1])
            move3 = int(move[3])
            if abs(move1 - move3) > 1 or abs(move1 - move3) == 0:
                uncapture_pawn_moves.remove(move)
        return {
            "back": legal_pawn_moves,
            "uncapture": uncapture_pawn_moves
        }

    def get_uncapture_moves(self, fen_pos: str, moves: list) -> list:
        """ Return a list of FEN states that can be possible "uncapture" moves """

        fen_numpy = MoveGenerator.board_numpy(fen_pos)
        player = fen_pos.split()[1]
        opponent = "w" if player == "b" else "b"

        # All chess pieces
        pieces = ['P'] * 8 + ['R'] + ['N'] + ['B'] + ['Q'] + ['K'] + ['B'] + ['N'] + ['R']

        # Fetch pieces already on the board
        if opponent == 'b':
            pieces = [piece.lower() for piece in pieces]
            pieces_on_board = [character for character in fen_pos.split()[0] if character.islower()]
        else:
            pieces_on_board = [character for character in fen_pos.split()[0] if character.isupper()]

        # Pieces not on the board
        for piece in pieces_on_board:
            pieces.remove(piece)

        # The same pieces will generate same uncapture states, so eliminate duplicates
        uncapture_pieces = list(set(pieces))

        previous_fens = []

        # Outer loop for each move
        for move in moves:

            # Play the reverse chess move
            board = ChessBoard(fen_pos)
            board.push_san(move)

            # For each piece for the current move
            for piece in uncapture_pieces:

                # Split fen into chess board rows
                fen_arr = board.fen().split()
                rows_list = fen_arr[0].split('/')

                # Retrieve the row string and column to insert the uncapture piece
                row = rows_list[8 - int(move[1])]
                column_index = self.map_fen[move[0]]

                # Convert the row string into list of characters for easy string manipulation
                row = MoveGenerator.board_numpy(row)[0]

                # Add the uncapture piece
                row[column_index] = piece

                # Update the fen
                num_count = 0
                string = ""
                for char in row:
                    if char == '-':
                        num_count += 1
                    else:
                        string = string + (str(num_count) if num_count > 0 else "") + char
                        num_count = 0
                if num_count > 0:
                    string = string + str(num_count)

                rows_list[8 - int(move[1])] = string
                new_fen = "/".join(rows_list)
                fen_arr[0] = new_fen
                new_fen = " ".join(fen_arr)
                previous_fens.append((move, new_fen))

        return previous_fens

    def get_moves(self, fen_pos: str):
        fen_pos = fen_pos.split()
        fen_pos[1] = "w" if fen_pos[1] == "b" else "b"
        fen_pos = " ".join(fen_pos)
        board = ChessBoard(fen_pos)

        legal = self.get_legal_moves(fen_pos)

        pawns = self.get_pawn_moves(fen_pos)
        uncapture_fens = self.get_uncapture_moves(board.fen(), legal) + self.get_uncapture_moves(board.fen(),
                                                                                                 pawns["uncapture"])

        pawns_back = pawns["back"]
        legal_fens = []
        pawns_back_fen = []

        for move in legal:
            board = ChessBoard(fen_pos)
            board.push_san(move)

            legal_fens.append((move, board.fen()))

        for move in pawns_back:
            board = ChessBoard(fen_pos)
            board.push_san(move)
            pawns_back_fen.append((move, board.fen()))

        return {"legal": legal_fens, "pawn": pawns_back_fen, "uncapture": uncapture_fens}

    def get_all_moves(self, position):
        validated_states = {"legal": [], "pawn": [], "uncapture": []}
        for move_type, moves in self.get_moves(position).items():
            for move, fens in moves:
                move = move[2:] + move[:2]

                fen = fens.split()
                fen[1] = "b" if fen[1] == "w" else "w"
                fen = " ".join(fen)
                board = chess.Board(fen)
                if board.is_valid():
                    legal = [uci(x).replace("x", "") for x in LegalMoves(board).to_array()]
                    if move in legal:
                        validated_states[move_type].append((move, fens))
        return validated_states
