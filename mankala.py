def index2player(index):
    return index//7


def is_current_player(index, player):
    return index2player(index) == player


def get_matching_hole(index):
    dist_from_bank, side = index % 7, index//7
    return 7-dist_from_bank+(1-side)*7


class Mankala:
    def __init__(self):
        """
        Indexes 0, 7 are the goals.
        0-6  player 1
        7-13 player 2
        """
        self.move_number = 1
        self.current_player = 0
        # This is labeled clockwise (down)
        # so we will progress by going backwards.
        # this representation is the easiest to code.
        self.board = [0, 4, 4, 4, 4, 4, 4] * 2
        self.log = {

        }
        self.game_over = False
        self.winner = None

    def reset(self):
        self.move_number = 1
        self.current_player = 0
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
        # 0 -> skip 7
        # 1 -> skip 0
        skip_bank = (1-self.current_player) * 7
        index -= 1
        if skip_bank == 0 and index == 0:
            index = 13
        if skip_bank == 1 and index == 7:
            index = 8
        return index

    def validate_move(self, index, player=None):
        if player is None:
            player = self.current_player

        if index2player(index) != player:
            raise Exception("Invalid Move. That is the second player's territory.")

        if self.game_over:
            raise Exception("Game is over. Cannot play further moves.")

    def get_side_marbles(self, player):
        return sum(self.board[player*7:player*7+7])

    def make_move(self, current_index, verbose=True):
        self.validate_move(current_index)
        save_start = current_index

        amount = self.board[current_index]
        self.board[current_index] = 0
        while amount >= 1:
            """Progress (counter-clockwise) and lay down the marbles"""
            current_index = self.loop(current_index)
            self.board[current_index] += 1
            amount -= 1

        """ Rule 3. If you land in enemy turf on an empty (now 1) hole, the enemy takes
            all the marbles in the matching hole on your side into their bank."""
        rule_3 = False
        if not is_current_player(current_index, self.current_player) and self.board[current_index] == 1:
            rule_3 = True
            # get enemy side
            opponent = int(not self.current_player)
            # find matching hole
            matching_hole = get_matching_hole(current_index)
            # move all the marbles from the matching hole to the
            # enemy's bank
            self.board[opponent*7] += self.board[matching_hole]
            self.board[matching_hole] = 0

        """ Landing in your own bank giving you another move.
        """
        change_move = True
        if current_index == self.current_player * 7:
            change_move = False

        if verbose:
            print(f"Player {self.current_player} played {save_start%7}")
            print(f"[{self.board[7]}]{self.board[8:14]}\n   {self.board[6:0:-1]}[{self.board[0]}]")

        if not change_move:
            special = "Extra Move"
        elif rule_3:
            special = "Rule 3, steal."
        else:
            special = "nothing"

        self.log[self.move_number] = {
            "player": self.current_player,
            "move": save_start,
            "special event": special
        }

        if change_move:
            self.current_player = int(not self.current_player)
        self.move_number += 1


''' Tests '''
game = Mankala()
game.make_move(6)
game.make_move(10)
game.reset()

