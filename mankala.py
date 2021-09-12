def index2player(index):
    return index//7


class Mankala:
    def __init__(self):
        """
        Indexes 0, 7 are the goals.
        0-6  player 1
        7-13 player 2
        """
        self.current_player = 0
        # This is labeled clockwise (down)
        # so we will progress by going backwards.
        # this representation is the easiest to code.
        self.board = [0, 4, 4, 4, 4, 4, 4] * 2
        self.log = {

        }

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

    def make_move(self, start_location, verbose=True):
        if index2player(start_location) != self.current_player:
            raise Exception("Invalid Move. That is the second player's territory.")
        amount = self.board[start_location]
        self.board[start_location] = 0
        while amount >= 1:
            """
            Progress (counter-clockwise) and lay down the marbles
            """
            start_location = self.loop(start_location)
            self.board[start_location] += 1
            amount -= 1

        if verbose:
            print(f"{self.current_player = }")
            print(f"[{self.board[7]}]{self.board[8:14]}\n   {self.board[6:0:-1]}[{self.board[0]}]")

        self.current_player = int(not self.current_player)

