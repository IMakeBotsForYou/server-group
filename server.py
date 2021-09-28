"""Server for multi-threaded (asynchronous) chat application."""
import mancala
from mancala import Mancala as Game
import _thread
from helper_functions import *

# global parameters
matchmaking_modes = ["lobbies", "fast_queue"]
params = {
    "game_id": 0,
    "verbose": True,
    "serverup": True,
    "timeout": 2,  # 5 seconds,
    "matchmaking mode": "lobbies"
}
queue = []
games = {

}
game_logs = {

}


def end_game(game_id):
    game = games[game_id]["game"]

    users = [clients[client]["name"] for client in games[game_id]["users"]]
    winner = game.winner

    for move in game.log:
        """
        [FIX]
        This part had "user" instead of "player". idk why, guess i was tired.
        also the try catch just made it so i didn't see this error straight away
        """
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        if game.log[move]["move"] != "Surrender":
            # The player is already updated. So this is unneeded and will cause an error.

            game.log[move]["player"] = users[game.log[move]["player"]]
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    first_p = {
        "type": "Game Over",
        "won": winner == 0,
        "log": game.log
    }
    second_p = {
        "type": "Game Over",
        "won": winner == 1,
        "log": game.log
    }

    try:
        p1 = games[game_id]["users"][0]
        send(p1, first_p)
    except Exception as e:
        print(e)
    try:
        p2 = games[game_id]["users"][1]
        send(p2, second_p)
    except Exception as e:
        print(e)


def send(client, obj):
    obj_str = json.dumps(obj)
    data = (msg_len(obj_str, 5) + obj_str).encode()
    client.send(data)


def inactivity_func(time_to_respond, client):
    print("started inactivity func")
    start_time = time.time()
    time.sleep(time_to_respond)
    if clients[client]["last_response"] <= start_time:
        # the user didn't answer
        kick_from_game(client, f"Received no response for {time_to_respond} seconds. "
                               f"Kicked for inactivity.")
        return  # ?


def send_board_update(game_id):
    board = games[game_id]["game"].board
    flipped_board = mancala.flip_board(board)
    current_player = games[game_id]["game"].current_player

    first_p = {
        "type": "Board Update",
        "board": board,
        "your turn": current_player == 0
    }
    second_p = {
        "type": "Board Update",
        "board": flipped_board,
        "your turn": current_player == 1
    }

    # open timeout thread for the user that needs to answer
    print("wha")
    _thread.start_new_thread(inactivity_func, (params["timeout"], games[game_id]["users"][current_player]))
    # TODO add an option for no countdown

    try:
        p1 = games[game_id]["users"][0]
        send(p1, first_p)
    except Exception as e:
        print(e)
    try:
        p2 = games[game_id]["users"][1]
        send(p2, second_p)
    except Exception as e:
        print(e)


def send_error(user, data, errtype="None"):
    jsonobj = {
        "type": "Error",
        "errtype": errtype,
        "data": data,
    }
    send(user, jsonobj)


def simple_message(user, msgtype, data, additional_args=None):
    if additional_args is None:
        additional_args = {}

    message = {
        "type": msgtype,
        "data": data
    }
    for arg in additional_args:
        message[arg] = additional_args[arg]

    send(user, message)


def join_game(game_id, user_socket):
    if game_id not in games:
        raise KeyError("Invalid game ID")
    if len(games[game_id]["users"]) == 1:
        games[game_id]["users"].append(user_socket)
        clients[user_socket]["current game"] = game_id
        send_board_update(game_id)
    else:
        a, b = [clients[x]["name"] for x in games[game_id]["users"]]
        raise IndexError(f"This game has already began, between {a} and {b}")


def initialize_game(host):
    game_id = params["game_id"]
    games[game_id] = {
        "game": Game(game_id),
        "users": [host]
    }
    clients[host]["current game"] = game_id
    params["game_id"] += 1


def matchmaking():
    while params["serverup"]:
        if len(queue) > 1:
            # get game id
            idnum = params["game_id"]

            # get first 2 users in queue
            users = queue.pop(0), queue.pop(0)
            clients[users[0]]["current game"] = idnum
            clients[users[1]]["current game"] = idnum
            # create game and save it in the games dictionary
            games[idnum] = {
                "game": Game(idnum),
                "users": users
            }
            # inc the next game id by 1
            params["game_id"] += 1
            # notify the 2 users of game start.
            # first user to join the queue gets first move.
            send_board_update(idnum)


def accept_incoming_connections():
    """
    First checks if a connection is a server-scanner or a client.
    If it's a user, it accepts the connection and sends them a welcome message.
    Then, we start a thread for that user and handle their input.
    """
    makingmode = params["matchmaking mode"]
    if makingmode == "fast_queue":
        # matchmaking_thread = Thread(target=matchmaking, daemon=True)
        # matchmaking_thread.start()
        _thread.start_new_thread(matchmaking, ())

    while params["serverup"]:
        # Accept the user
        client, client_address = SERVER.accept()

        print(f"{client_address} has connected.")
        addresses[client] = client_address
        _thread.start_new_thread(handle_client, (client,))
        # Thread(target=handle_client, args=(client,), daemon=True).start()
        print(f"Starting thread for {client_address}")


"""
def inactivity_check(client):
    Checks the time between the user's last message and now,
    if over the specified time, send a message.
    :param client: client being checked
    :return: None
    current_time = int(time.time())
    try:
        if current_time - clients[client]["last response"] > params["timeout"]:
            if clients[client]["current game"] is None:
                # reset timeout counter
                clients[client]["last response"] = int(time.time())
            else:
                # The user is in a game.
                # Is it a game in progress?
                game_id = clients[client]["current game"]
                if games[game_id]["game"].game_over or len(games[game_id]["users"]) < 2:
                    # reset timeout counter
                    clients[client]["last response"] = int(time.time())
                else:
                    # The user is inactive during a game.
                    # is it their turn? the user user might be hogging their turn.

                    index_in_lobby = games[game_id]["users"].index(client)
                    [FIX]
                    Another problem I found is that if a user takes too long to respond,
                    for example 5 seconds; It will also kick the second user, obviously since
                    they aren't responding. 
                    To fix this, we now check if it is the current users turn. If not, we 
                    reset the LAST RESPONSE variable.
                    if games[game_id]["game"].current_player != index_in_lobby:
                        # reset counter
                        clients[client]["last response"] = int(time.time())
                    else:
                        kick_from_game(client,
                                       message=f"Received no response for {params['timeout']}s. "
                                               f"Kicked for inactivity.")

    except KeyError:
        # If there's an error then stop looping this
        [FIX]
        Added this print, to know when this happens.
        Apparently the stop loop thing doesnt work? i'm not sure.
        print(f"There was an error with the inactivity check function for {clients[client]['name']}")
        return "stop"
"""


def kick_from_game(client, message=None):
    in_game = clients[client]["current game"]
    if in_game is None:
        raise AttributeError("Cannot kick a user from a game if they're not in one.")
    else:
        """ Do we show the log to both users?
        """
        clients[client]["current game"] = None
        name = clients[client]["name"]

        players = games[in_game]["users"]

        """
        [FIX]
        This is less of a fix, and more of a fix-up.
        Before, the log_event function would log an event with the label 'Surrender'
        This could be inconvenient, since all the other events are marked
        with a number (the turn number).
        Now, it will input the event in the correct format ↓
        
        self.log[self.move_number] = {
            "player": int/str,
            "move": int/str,
            "special event": str
        }
        
        """
        events_so_far = len(games[in_game]["game"].log)
        games[in_game]["game"].log_event(events_so_far,
                                         {
                                             "player": clients[client]["name"],
                                             "move": "Surrender",
                                             "special event": "User has left the game."
                                         })
        if message:
            simple_message(client, msgtype="Notification",
                           data=message)

        user_kicked_index = (1 - players.index(client))
        games[in_game]["game"].winner = user_kicked_index

        end_game(in_game)

        players.remove(client)

        simple_message(players[0], msgtype="Notification",
                       data=f"{name} has quit your Lobby.")

        print(f"{name} has been kicked from lobby #{in_game}")


def handle_client(client):  # Takes client socket as argument.
    """
    Handles a single client connection.
    This is done by first registering a valid name.
    Then we handle every message, from normal, Commands everyone can see,
    and commands only the user can see.
    """
    try:
        simple_message(client, msgtype="Welcome", data="Choose a name!")
        name = client.recv(1024).decode()
        # if there's any keywords we want to ban
        # this might be useful if we have reserved keywords for system functions, like @ or !
        banned_words = ["join", "create"]
        names = [x["name"] for x in clients.values()]

        banned_words_used = [key_word for key_word in banned_words if name.find(key_word) != -1]
        banned_words_used += [x for x in names if name == x]
        while len(banned_words_used) != 0 or (len(name) > 32 or len(name) < 3):

            if len(name) > 32 or len(name) < 3:
                data = "Name must be between 3-32 characters"
            else:
                data = f"Invalid nickname. Unavailable key words used: {banned_words_used}"

            send_error(client, data, errtype="Invalid Name")

            if name:
                print(f"Illegal login attempt: {name} || {banned_words_used}")
            name = client.recv(50).decode()
            banned_words_used = [key_word for key_word in banned_words if name.find(key_word) != -1]
            banned_words_used += [x for x in names if name == x]
        print(f"{client}\n has registered as {name}")

    except ConnectionResetError:  # 10054
        print("Client error'd out.")
        del addresses[client]
    except ConnectionAbortedError:
        # user checking ports
        del addresses[client]
        pass
    except UnicodeDecodeError:
        del addresses[client]
        pass
    else:
        clients[client] = {"name": name,
                           "last response": time.time(),
                           "games": {
                               "wins": 0,
                               "loses": 0
                           },
                           "current game": None}
        # "ping function": call_repeatedly(params["timeout"]*0.5, inactivity_check, client)}

        if params["matchmaking mode"] == "queue":
            queue.append(client)

        name = clients[client]["name"]

        while params["serverup"]:

            '''
            here we get data from the client
            '''
            print(client.recv(1024, MSG_PEEK))
            try:
                data = json.loads(client.recv(1024))
            except json.decoder.JSONDecodeError:
                send_error(client, errtype="Bad Message", data="JSON Parse Failure.")
                continue
            try:
                msg_type = data["type"]
            except KeyError:
                send_error(client, errtype="Bad Message", data="No message type.")
                continue

            # At this point we may assume that we recieved a valid message from the user.

            clients[client]["last response"] = time.time()

            if params["matchmaking mode"] == "lobbies":
                if msg_type == "Start Game":
                    if clients[client]["current game"]:
                        send_error(errtype="Bad Request",
                                   data="You are already in a lobby. To create a new one leave your current one.")
                    else:
                        initialize_game(client)
                        simple_message(client, msgtype="Success",
                                       data=f"You have successfully initialized a game with id {params['game_id'] - 1}",
                                       additional_args={"game_id": params['game_id'] - 1})

                # TODO Uriiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii here you can add the tournament match_making
                if msg_type == "Restart Game":
                    if clients[client]["current game"] is not None:
                        game_id = clients[client]["current game"]
                        # if user is the owner of the game:
                        # if client != games[game_id]["users"][0]:
                        #     send_error(client, errtype="Permission Error",
                        #                data="You are not the owner of the game. "
                        #                     "Only the owner of the game can restart it.")

                        if games[game_id]["game"].game_over:

                            games[game_id]["game"].reset()
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully restarted game #{game_id}")
                            if len(games[game_id]["users"]) > 1:
                                simple_message(games[game_id]["users"][1], msgtype="Notification",
                                               data="Your game has been restarted.")
                                send_board_update(game_id)
                        else:
                            send_error(client, errtype="Permission Error",
                                       data="Cannot reset a game in progress."
                                            "A game can only be restarted after it has ended.")

                #
                if msg_type == "Join Game":
                    try:
                        game_id = data["game_id"]
                    except KeyError:
                        send_error(client, errtype="Bad Message", data="'game id' field missing in Join Game message")
                    else:
                        try:
                            join_game(game_id, client)
                        except IndexError:
                            send_error(client, errtype="Join Error",
                                       data=f"Game #{game_id} is full.")
                        except KeyError:
                            send_error(client, errtype="Join Error",
                                       data=f"#{game_id} is an invalid game ID.")
                        else:
                            opponent_socket = games[game_id]["users"][0]
                            opponent_name = clients[opponent_socket]["name"]
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully joined game #{game_id}, "
                                                f"your opponent is {opponent_name}")

                            simple_message(opponent_socket, msgtype="Notification",
                                           data=f"{name} has joined your Lobby.")

                #
                if msg_type == "Quit Game":
                    in_game = clients[client]["current game"]
                    try:
                        kick_from_game(client)
                    except AttributeError:
                        send_error(client, errtype="Bad Request", data="Can't quit game if user is not in a game.")
                    else:
                        simple_message(client, msgtype="Success",
                                       data=f"You have successfully quit game #{in_game}")

            #
            if msg_type == "Game Move":
                try:
                    play_index = data["index"]
                except KeyError:
                    send_error(client, errtype="Bad Message", data="'game id' field missing in Join Game message")
                    continue

                """
                [FIX]
                Regarding the fix below, this IF statement should take care of it.
                But you can never be too sure.
                """
                if clients[client]["current game"] is None:
                    continue
                try:
                    games[clients[client]["current game"]]["game"].make_move(play_index, adjust_index=True)
                except ValueError:
                    send_error(client, "You've made an invalid move. It is still your turn.",
                               errtype="Invalid Move")
                except IndexError as e:
                    # Selected an empty hole.
                    send_error(client, str(e) + " It is still your turn.", errtype="Invalid Move")
                except TypeError as e:
                    send_error(client, "Moves have to be ints. It is still your turn.", errtype="Invalid Move")
                except AttributeError:
                    # Someone won
                    end_game(clients[client]["current game"])
                except KeyError:
                    """
                    [FIX] ?
                    Also, if the client would send {Game Move} messages while not in a game,
                    or after being kicked, it would give a KeyError for 
                    games[clients[client]["current game"]]["game"]
                    This is now handled. 
                    """
                    send_error(client, "Something went wrong.", errtype="Invalid Move")
                else:
                    send_board_update(clients[client]["current game"])

            #
            # except Exception as e:
            #     send_error(client, errtype="Server Error", data=str(e))


def broadcast(msg, send_to=None):
    """Broadcasts a message to all the clients."""
    if not send_to:
        send_to = clients
    for sock in send_to:
        try:
            send(sock, msg)
        except ConnectionResetError:  # 10054
            pass


if __name__ == '__main__':
    HOST = ""
    PORT = 45_000

    mode = input("WAN server or LAN server?  (wan/lan) > ").lower()
    while mode not in ["wan", "lan"]:
        print("Invalid.")
        mode = input("WAN server or LAN server?  (wan/lan) > ").lower()

    """
    If mode is lan, then choose a random port and host on NAT
    If mode is wan, assume user has set up port forwarding,
    and request a port to host the server on.
    """
    ip, port = 0, 0
    stop_calling = None
    if mode == "lan":
        # LAN server, pick a random port.
        PORT = 0
        SERVER = socket(AF_INET, SOCK_STREAM)
        ADDR = (HOST, PORT)
        SERVER.bind(ADDR)
        ip = gethostbyname(gethostname())
        port = SERVER.getsockname()[1]

    else:
        SERVER = socket(AF_INET, SOCK_STREAM)
        port = input("Enter PortForwarding PORT > ")
        while not port.isnumeric():
            port = input("Enter PortForwarding PORT > ")
        port = int(port)
        ADDR = (HOST, port)
        SERVER.bind(ADDR)

    clients = {}
    addresses = {}

    with open("port.txt", "w+") as f:
        f.write(str(port))

    SERVER.listen(5)
    print(f"---------------------------------------------------------")
    print(f"Starting {mode} server, on {ip}:{port}, @ {time.ctime(time.time())}")
    print("Waiting for connection...")

    accept_incoming_connections()

    SERVER.close()
    stop_calling()
    print(f"END LOG")
    print(f"---------------------------------------------------------")
