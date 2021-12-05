from copy import deepcopy as copy


def index2player(index):
    return index // 7


def is_current_player(index, player):
    return index2player(index) == player


def get_matching_hole(index):
    dist_from_bank, side = index % 7, index // 7
    return 7 - dist_from_bank + (1 - side) * 7


def flip_board(board):
    side1, side2 = board[0:7], board[7:14]
    return side2 + side1


class Mancala:
    def __init__(self, id, board=None):
        """
        Indexes 0, 7 are the goals.
        0-6  player 1
        7-13 player 2
        """
        self.id = id
        self.move_number = 1
        self.current_player = 0
        # This is labeled clockwise (down)
        # so we will progress by going backwards.
        # this representation is the easiest to code.
        if board is None:
            self.board = [0, 4, 4, 4, 4, 4, 4] * 2
        else:
            self.board = board
        # self.board = [0, 4, 4, 4, 4, 4, 4] + [-1, -1, -1, 4, 0, 0]
        # ^ ^ ^
        # game.make_move(5)
        # game.make_move(10)
        # to check winner check.
        #
        self.log = {

        }
        self.history = [copy(self.board)]

        self.game_over = False
        self.winner = None

    def log_event(self, label, data):
        self.log[label] = data

    def set_winner(self, player):
        self.game_over = True
        self.winner = player

    def reset(self):
        self.move_number = 1
        self.current_player = 0
        # goes up instead of down
        # self.board = [4, 4, 4, 4, 4, 4, 0] * 2
        self.board = [0, 4, 4, 4, 4, 4, 4] * 2
        self.log = {
        }
        self.game_over = False
        self.winner = None

    def loop(self, index):
        """
        :param index: The current index to jump from
        :return: The next correct index
        """
        # goes up instead of down
        # 0 -> skip 14
        # 1 -> skip 7
        # skip_bank = (2-self.current_player) * 7
        # index += 1
        #
        # if skip_bank == 14 and index == 14:
        #     index = 0
        # if skip_bank == 7 and index == 7:
        #     index = 8



        # 0 -> skip 7
        # 1 -> skip 0
        skip_bank = (1 - self.current_player) * 7
        index -= 1

        if index == -1:
            index = 13

        if skip_bank == 0 and index == 0:
            index = 13
        if skip_bank == 7 and index == 7:
            index = 6
        return index

    def validate_move(self, index, player=None):
        if player is None:
            player = self.current_player
        self.check_win()
        if self.game_over:
            raise AttributeError("Game is over. Cannot play further moves.")

        if index2player(index) != player:
            raise ValueError("Invalid Move. That is the second player's territory.")

        if self.board[index] == 0:
            raise IndexError(f"Hole #{index % 7} ({index}) is empty!")

    def empty_side(self, side):
        for index in range(side * 7 + 1, side * 7 + 7):
            self.board[index] = 0

    def get_side_marbles(self, player, include_bank=False):
        add = 0
        if include_bank:
            add = self.board[player * 7]
        return sum(self.board[player * 7 + 1:player * 7 + 7]) + add

    def check_win(self):
        side_a, side_b = self.get_side_marbles(0), self.get_side_marbles(1)
        checkwinner = False
        if side_a == 0:
            self.board[0] += side_b
            self.empty_side(1)
            checkwinner = True

        if side_b == 0:
            self.board[7] += side_a
            self.empty_side(0)
            checkwinner = True

        if checkwinner:
            self.game_over = True
            side_a, side_b = self.get_side_marbles(0, include_bank=True), self.get_side_marbles(1, include_bank=True)
            if side_a > side_b:
                self.winner = 0

            elif side_a < side_b:
                self.winner = 1
            else:
                self.winner = 2

    def make_move(self, current_index, verbose=True, adjust_index=False):
        """
        :param current_index: Index to play
        :param verbose: Print what happened
        :param adjust_index: Automatically flip the index (flip the board)
        :return:
        """
        if adjust_index:
            current_index += self.current_player * 7
        self.validate_move(current_index)

        save_start = current_index
        amount = self.board[current_index]
        self.board[current_index] = 0

        while amount >= 1:
            """Progress (counter-clockwise) and lay down the marbles"""
            current_index = self.loop(current_index)
            self.board[current_index] += 1
            amount -= 1
        """ Rule 3. If you land in an empty (now 1) hole, the enemy takes
            all the marbles in the matching hole on your side into your bank."""
        rule_3 = False
        # is_current_player(current_index, self.current_player) and
        if self.board[current_index] == 1 and current_index % 7 != 0:
            # find matching hole
            # ==========================================
            # GET MATCHING HOLE DOES NOT WORK WITH MINUS!
            # ==========================================
            matching_hole = get_matching_hole(current_index % 14)
            if self.board[matching_hole] != 0:
                rule_3 = True
                # move all the marbles from the matching hole to the
                # player's bank
                self.board[self.current_player * 7] += self.board[matching_hole]
                self.board[matching_hole] = 0

        """ Landing in your own bank giving you another move.
        """
        change_move = True
        if self.current_player == 1:
            print(current_index, self.current_player * 7)
        if current_index == self.current_player * 7:
            change_move = False

        self.check_win()
        if self.game_over:
            change_move = True

        special = ""
        if not change_move:
            special = "Extra Move"
        if rule_3:
            special = "Rule 3, steal."
        if self.game_over:
            if self.winner == 2:
                special += " Draw."
            else:
                special += f" Player {chr(ord('A') + self.winner)} won."
        # this else statement was screwing up the entire log
        if change_move and not rule_3 and not self.game_over:
            special = "nothing"

        # in case the game is won and there's no special (special will begin with a space)
        special = special.strip()

        if verbose:
            print(f"Player {self.current_player} played {save_start % 7}", end="")
            if special != "nothing":
                print(f", {special}")
            else:
                print('')

            print(f"[{self.board[0]}]{self.board[1:7]}\n   {self.board[13:7:-1]}[{self.board[7]}]")

        self.log[self.move_number] = {
            "player": self.current_player,
            "move": save_start,
            "special event": special
        }

        self.history.append(copy(self.board))

        if change_move:
            self.current_player = int(not self.current_player)
        self.move_number += 1

    def revert(self, turn):
        self.current_player = int(turn % 2 == 1)
        self.board = self.history[turn]
        self.history = self.history[:turn]
        for i in range(turn + 1, len(self.log)):
            del self.log[i]

    def eval_board(self):
        return self.get_side_marbles(0, include_bank=True) > self.get_side_marbles(1, include_bank=True)

    def json(self):
        return {
            "move number": self.move_number,
            "current player": self.current_player,
            "current board": self.board,
            "log": self.log
        }


import unittest


class TestMancala(unittest.TestCase):
    def test(self):
        board = Mancala(0)
        board.make_move(1)
        self.assertEqual(board.board, [1, 0, 4, 4, 4, 4, 4, 0, 4, 4, 4, 5, 5, 5])
        with self.assertRaises(ValueError):
            board.make_move(1)
        board.make_move(12)  # land in your own goal, get an extra turn
        board.make_move(11)


if __name__ == '__main__':
    unittest.main()
