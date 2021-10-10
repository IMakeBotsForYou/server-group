"""Server for multi-threaded (asynchronous) chat application."""
import mancala
from mancala import Mancala as Game
import _thread
from imports import *

# global parameters
matchmaking_modes = ["lobbies", "fast_queue"]
params = {
    "game_id": 0,
    "verbose": True,
    "serverup": True,
    "timeout": 5,  # 5 seconds,
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
        if game.log[move]["move"] != "Surrender":
            # The player is already updated. So this is unneeded and will cause an error.

            game.log[move]["player"] = users[game.log[move]["player"]]

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
    start_time = time.time()
    time.sleep(time_to_respond)
    if clients[client]["last_response"] <= start_time:
        # the user didn't answer
        try:
            kick_from_game(client, f"Received no response for {time_to_respond} seconds. "
                                   f"Kicked for inactivity.")
        except AttributeError as e:  # catches the error that it cannot kick a user from a game if it is not in one
            print(e)


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
    if not games[game_id]["slow_game"]:
        _thread.start_new_thread(inactivity_func, (params["timeout"], games[game_id]["users"][current_player]))

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


def msg_len(data, length=3):
    """
    :param length: length of output string
    :param data: The data we're getting the length of
    :return: Length of the encoded data, left-padded to be 3 digits long.
    """
    try:
        return str(len(data.encode())).zfill(length)
    except:
        return str(len(data)).zfill(length)  # already encoded


def join_game(game_id, user_socket):
    if game_id not in games:
        raise KeyError("Invalid game ID")
    if len(games[game_id]["users"]) == 1:
        games[game_id]["users"].append(user_socket)
        clients[user_socket]["current_game"] = game_id
        send_board_update(game_id)
    else:
        a, b = [clients[x]["name"] for x in games[game_id]["users"]]
        raise IndexError(f"This game has already began, between {a} and {b}")


def initialize_game(host, is_slow_game=False):
    game_id = params["game_id"]
    games[game_id] = {
        "game": Game(game_id),
        "users": [host],
        "slow_game": is_slow_game
    }
    clients[host]["current_game"] = game_id
    params["game_id"] += 1


def matchmaking():
    while params["serverup"]:
        if len(queue) > 1:
            # get game id
            idnum = params["game_id"]

            # get first 2 users in queue
            users = queue.pop(0), queue.pop(0)
            clients[users[0]]["current_game"] = idnum
            clients[users[1]]["current_game"] = idnum
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


def kick_from_game(client, message=None):
    in_game = clients[client]["current_game"]
    print(f"game over: {games[in_game]['game'].game_over}")
    if in_game is None:
        raise AttributeError("Cannot kick a user from a game if they're not in one.")
    elif not games[in_game]["game"].game_over:
        # if the user is in a game

        clients[client]["current_game"] = None
        name = clients[client]["name"]

        players = games[in_game]["users"]

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


def validate_user_message(client, data, has_logged_in=True):
    message_types = ["Login", "Game Move", "Quit Game", "Join Game", "Start Game", "Restart Game"]
    try:
        data = json.loads(data)
    except json.decoder.JSONDecodeError:
        send_error(client, errtype="Bad Message", data="JSON Parse Failure.")
        return False
    try:
        msg_type = data["type"]
        assert msg_type in message_types
    except KeyError:
        send_error(client, errtype="Bad Message", data="No valid message type.")
        return False
    except AssertionError:
        send_error(client, errtype="Bad Message",
                   data=f'Message type must be one of {", ".join(message_types)}')
        return False

    if not has_logged_in and msg_type != "Login":
        send_error(client, errtype="Bad Request", data="You have to be logged in first.")
        return false

    if msg_type == "Login":
        if has_logged_in:
            send_error(client, errtype="Bad Request", data="You are already logged in.")
            return False

        if "name" not in data:
            send_error(client, errtype="Bad Message", data="'name' field missing in Login message")
            return False

    if msg_type == "Game Move":
        try:
            index = data["index"]
            assert isinstance(index, int)
        except KeyError:
            send_error(client, errtype="Bad Message", data="'index' field missing in Game Move message")
            return False
        except AssertionError:
            send_error(client, errtype="Bad Message", data="'index' field must be int.")
            return False

    if msg_type == "Join Game":
        try:
            game_id = data["game_id"]
            assert isinstance(game_id, int)
        except KeyError:
            send_error(client, errtype="Bad Message", data="'game id' field missing in Join Game message")
            return False
        except AssertionError:
            send_error(client, errtype="Bad Message", data="'game id' field must be int.")
            return False

    return True


def handle_client(client):  # Takes client socket as argument.
    """
    Handles a single client connection.
    This is done by first registering a valid name.
    Then we handle every message, from normal, Commands everyone can see,
    and commands only the user can see.
    """
    try:
        taken_names = [x["name"] for x in clients.values()]
        simple_message(client, msgtype="Welcome", data="Choose a name!", additional_args={"Taken names": taken_names})
        unparsed = client.recv(1024).decode()
        logged_in = False
        name = ""
        # ask for name until you recieve a valid message
        while not logged_in:
            # This was a while True loop making the code afterwards unreachable.
            while not validate_user_message(client, unparsed, has_logged_in=False):
                # added has_logged_in=False, default is True.
                unparsed = client.recv(1024).decode()

            message = json.loads(unparsed)
            name = message["name"]

            if name in taken_names:
                send_error(client, data="This name is already taken", errtype="Invalid Name")
            else:
                logged_in = True

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
                           "last_response": time.time(),
                           "games": {
                               "wins": 0,
                               "loses": 0
                           },
                           "current_game": None}

        if params["matchmaking mode"] == "queue":
            queue.append(client)

        name = clients[client]["name"]

        while params["serverup"]:

            '''
            here we get data from the client
            '''
            print(client.recv(1024, MSG_PEEK))
            unparsed = client.recv(1024)
            valid = validate_user_message(client, unparsed)

            if not valid:
                continue

            data = json.loads(unparsed)
            msg_type = data["type"]
            # At this point we may assume that we received a valid message from the user.

            clients[client]["last_response"] = time.time()

            if params["matchmaking mode"] == "lobbies":
                if msg_type == "Start Game":
                    if clients[client]["current_game"]:
                        send_error(client, errtype="Bad Request",
                                   data="You are already in a lobby. To create a new one leave your current one.")
                    else:
                        if "slow_game" in data:
                            initialize_game(client, data["slow_game"])
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully initialized a game with id {params['game_id'] - 1}, "
                                                f"the game doesn't have a time response limit",
                                           additional_args={"game_id": params['game_id'] - 1})
                        else:
                            initialize_game(client)
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully initialized a game with id {params['game_id'] - 1}",
                                           additional_args={"game_id": params['game_id'] - 1})

                # TODO Uriiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii here you can add the tournament match_making
                if msg_type == "Restart Game":
                    if clients[client]["current_game"] is not None:
                        game_id = clients[client]["current_game"]
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
                            send_error(client, errtype="Bad Request",
                                       data="Cannot reset a game in progress."
                                            "A game can only be restarted after it has ended.")

                #
                if msg_type == "Join Game":
                    game_id = data["game_id"]
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
                    in_game = clients[client]["current_game"]
                    try:
                        kick_from_game(client)
                    except AttributeError:
                        send_error(client, errtype="Bad Request", data="Can't quit game if user is not in a game.")
                    else:
                        simple_message(client, msgtype="Success",
                                       data=f"You have successfully quit game #{in_game}")

            #
            if msg_type == "Game Move":
                play_index = data["index"]
                if clients[client]["current_game"] is None:
                    continue
                try:
                    games[clients[client]["current_game"]]["game"].make_move(play_index, adjust_index=True)
                except ValueError:
                    send_error(client, "You've made an invalid move. It is still your turn.",
                               errtype="Invalid Move")
                except IndexError as e:
                    # Selected an empty hole.
                    send_error(client, str(e) + " It is still your turn.", errtype="Invalid Move")
                except TypeError:
                    send_error(client, "Moves have to be ints. It is still your turn.", errtype="Invalid Move")
                except AttributeError:
                    # Someone won
                    end_game(clients[client]["current_game"])
                except KeyError:
                    """
                    If the client would send {Game Move} messages while not in a game,
                    or after being kicked, it would give a KeyError for 
                    games[clients[client]["current_game"]]["game"]
                    This is now handled. 
                    """
                    send_error(client, "Something went wrong.", errtype="Invalid Move")
                else:
                    send_board_update(clients[client]["current_game"])

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
            print("Client has disconnected")


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
