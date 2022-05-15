import time
import math
import random

import chess
from stockfish import Stockfish

from heuristics import Heuristics
from move_generator import MoveGenerator

stockfish_path = "stockfish_14.1_win_x64_avx2/stockfish_14.1_win_x64_avx2.exe"


# Most of this cell is rip-off from python-chess library
# We overwrite existing classes and functions for our requirements


class State:
    def __init__(self, fen: str, parent: str = None, move: str = None) -> None:
        self.fen = fen
        self.parent = parent
        self.children = []

    def add_child(self, fen_position: str) -> list:
        self.children.append(fen_position)
        return self.children

    @property
    def board(self) -> None:
        display(chess.Board(self.fen))
        return

    def __str__(self) -> str:
        return f"{self.fen}: {[str(x.fen) for x in self.children]}"

    def __repr__(self) -> str:
        return self.__str__()


class GameState:

    def __init__(self, initial_state: str = None) -> None:

        self.initial = None
        self.board = None

        if initial_state:
            self.update_initial(initial_state)

        self.stockfish = Stockfish(stockfish_path)
        self.stockfish.set_depth(8)

        self.heur = Heuristics()
        self.move_generator = MoveGenerator()

    @property
    def player(self) -> str:
        """ Returns the player (w/b)"""
        return self.board.fen().split()[1]

    @property
    def display_board(self) -> None:
        print(f"{'White' if self.player == 'w' else 'Black'} to move")
        display(self.board)
        return

    def update_initial(self, position) -> None:
        self.initial = State(position)
        self.board = chess.Board(position)
        return

    def get_all_moves(self) -> None:
        # Main function to get all possible backtrack moves
        # self.get_pawn_moves()
        # self.get_legal_reverse_moves()
        # self.get_special_moves()

        return self.move_generator.get_all_moves(self.board.fen())

    def flip_board(self) -> None:
        # Flips the board and player's turn
        self.board = self.board.mirror()
        self.display_board()

    def get_puzzles(self, max_depth=6):
        _start = time.time()
        total_states = 0

        position = self.initial.fen

        trim = True
        queue = [position]

        default_dict = {
            "legal": [],
            "pawn": [],
            "uncapture": [],
        }

        results = {
            "legal": [],
            "pawn": [],
            "uncapture": [],
        }

        for i in range(1, max_depth):
            count = 0
            temp_queue = []
            print("Depth: ", i)
            while queue:
                position = queue.pop()
                move_dict = self.move_generator.get_all_moves(position)
                self.stockfish.set_fen_position(position)
                filtered = {"legal": [], "pawn": [], "uncapture": []}
                centis = {"legal": [], "pawn": [], "uncapture": []}
                heurs = {"legal": [], "pawn": [], "uncapture": []}

                player = "w" if position.split()[1] == "b" else "b"

                for move_type, moves in move_dict.items():
                    for move, fen in moves:
                        # move = move[2:] + move[:2]
                        fen = fen.split()
                        fen[1] = "b" if fen[1] == "w" else "w"
                        fen = " ".join(fen)

                        self.stockfish.set_fen_position(fen)
                        top_moves = self.stockfish.get_top_moves(1)
                        if move in top_moves[0]["Move"]:
                            count += 1
                            val = self.heur.get_all_heuristics(fen)

                            if not top_moves[0]["Centipawn"]:
                                if not top_moves[0]["Mate"]:
                                    continue
                                top_moves[0]["Centipawn"] = math.inf * top_moves[0]["Mate"]

                            filtered[move_type].append((move, fen, top_moves[0]["Centipawn"], val))
                            centis[move_type].append(top_moves[0]["Centipawn"])
                            heurs[move_type].append(val[1])

                position = position.split()
                position[1] = "w" if position[1] == "b" else "b"

                player_multiplier = 1 if player == "w" else -1

                for move_type in default_dict.keys():
                    temp_filtered = filtered[move_type]
                    if centis[move_type]:
                        if player_multiplier * math.inf in centis[move_type]:
                            temp_filtered = [state for state in temp_filtered if
                                             state[2] == player_multiplier * math.inf]
                        else:
                            centis[move_type].sort()
                            if player_multiplier == 1:
                                centi_threshold = centis[move_type][-1] * 0.8
                            else:
                                centi_threshold = centis[move_type][0] * 0.8
                            centi_threshold = 0
                            if abs(centi_threshold) != math.inf:
                                temp_filtered = [state for state in temp_filtered
                                                 if abs(state[2]) > abs(centi_threshold)]
                    if heurs[move_type]:
                        heurs[move_type].sort()
                        heur_threshold = heurs[move_type][-1] * 0.8 * 0
                    else:
                        heur_threshold = 0
                    if i < 3:
                        temp_filtered = [state for state in temp_filtered if state[3][1] > 0.1]
                    if len(temp_filtered) > 5 and trim:
                        temp_filtered.sort(key=lambda x: x[3][1])
                        temp_filtered = temp_filtered[:5]
                    total_states += len(temp_filtered)
                    if temp_filtered and i > 1 and i % 2 == 1:
                        for row in temp_filtered:
                            results[move_type].append((i, row))
                    temp_filtered = [move[1] for move in temp_filtered]
                    temp_queue.extend(temp_filtered)
                    filtered[move_type] = temp_filtered

            print(f"Total good puzzles at depth: {i} are {count}")
            queue = temp_queue
        print(time.time() - _start)

        puzzles = []
        for move_type in results:
            temp = random.choices(results[move_type], k=min(len(results[move_type]), 2))
            puzzles.extend([puzzle[1][1] for puzzle in temp if puzzle[0] > 2])
        return results


if __name__ == '__main__':
    generator = GameState("6R1/1ppk1Np1/p6p/2b5/8/PnP5/1P3PPP/6K1 b - - 0 29")
    puzzles = generator.get_puzzles()
    print(puzzles)
    legal = puzzles["legal"]
    uncapture = puzzles["uncapture"]

    print(len(legal))
    print(len(uncapture))

    max = 0
    top_puzzles = []

    for i in range(0, 2):
        max = 0
        if len(legal) > 0:
            for j in range(len(legal)):
                if max < legal[j][1][3][1]:
                    top_fen = legal[j][1][1]
                    max = legal[j][1][3][1]
                    index = j
            top_puzzles.append(top_fen)
            legal.remove(legal[index])
    print(len(top_puzzles))

    for i in range(0, 2):
        max = 0
        if len(uncapture) > 0:
            for j in range(len(uncapture)):
                if max < uncapture[j][1][3][1]:
                    top_fen = uncapture[j][1][1]
                    max = uncapture[j][1][3][1]
                    index = j
            top_puzzles.append(top_fen)
            uncapture.remove(uncapture[index])

    print(top_puzzles)
