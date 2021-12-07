"""Server for multi-threaded (asynchronous) chat application."""
from imports import *
import _thread
# global parameters
matchmaking_modes = ["lobbies", "queue"]
params = {
    "game_id": 0,
    "verbose": True,
    "serverup": True,
    "timeout": 4,  # 1 seconds,
    "matchmaking mode": "queue",  # "queue"
    "delay": 3
}

competitors = []
games = {

}
game_logs = {
    time.sleep(seconds)

}
leader_board = {}

def log(data, prefix=None):
    #   Pretty print
    #   data: The content to print
    #   prefix: will appear as [prefix] before the message
    #   Example:
    #   [Log] 12:00:00 your message

    if prefix is None:
        prefix = "Log"
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{prefix}]\t{current_time}  {data}")

FLAG = False


def end_game(game_id):
    """
    ends the game when exception is raised.
    """
    global leader_board
    winner = games[game_id]["game"].winner
    for client in games[game_id]["users"]:
        if client not in leader_board:
            leader_board.update({client: 0})
    if winner == 2:
        leader_board[games[game_id]["users"][0]] += 1
        leader_board[games[game_id]["users"][1]] += 1
    else:
        leader_board[games[game_id]["users"][winner]] += 2

    game = games[game_id]["game"]
    usernames = [clients[client]["name"] for client in games[game_id]["users"]]
    winner = game.winner
    # Adjust the log so it includes player names and adjusted indexes
    try:
        for move_num, move in game.log.items():
            # If the player is 1, this will remove 7 from the move. 13->6, 8->1
            adjust_index = move["player"]*7
            move["move"] -= adjust_index

            move["player"] = usernames[move["player"]]

            # Change "Player A/B won" to the user's name.
            if move["special event"][-4:] == 'won.':
                winner_socket = games[game_id]["users"][winner]
                # using regex bc there might be a special event like rule 3 or extra move as well in the mix :)
                move["special event"] = sub(move["special event"], 'A|B', f"{clients[winner_socket]['name']} won.")

    except TypeError:
        log(prefix="Err", data="Error adjusting logs. Sending them as is.")

    for move in game.log:
        if game.log[move]["move"] != "Surrender":
            # The player is already updated. So this is unneeded and will cause an error.
            game.log[move]["player"] = users[game.log[move]["player"]]
            # If the player is 1, this will remove 7 from the move. 13->6, 8->1
            adjust_index = move["player"]*7
            move["move"] -= adjust_index

            move["player"] = usernames[move["player"]]

            # Change "Player A/B won" to the user's name.
            if move["special event"][-4:] == 'won.':
                winner_socket = games[game_id]["users"][winner]
                # using regex bc there might be a special event like rule 3 or extra move as well in the mix :)
                move["special event"] = sub(move["special event"], 'A|B', f"{clients[winner_socket]['name']} won.")

    
    # else:
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
    # sort leaderboard
    new_leader = dict(reversed(sorted(leader_board.items(), key=lambda item: item[1])))

    global FLAG
    while FLAG:
        pass # wait

    FLAG=True
    print("Leaderboard:")
    leader_board = new_leader
    for i, client in enumerate(leader_board):
        print(f"{i + 1}.{clients[client]['name']}: {leader_board[client]}")
    FLAG=False

    competitors.append(games[game_id]["users"][0])
    competitors.append(games[game_id]["users"][1])

    log(prefix="END", data="Trying to send logs")
    try:
        p1 = games[game_id]["users"][0]
        send(p1, first_p)
    except Exception as e:
        log(data=f"end_game(), line 65 | {e}",prefix="Err")
        # print(e)
    else:
        log(prefix="SUCCESS", data=f"Sent to {clients[p1]['name']}")
        log(prefix="JSONLOG", data=f"{len(json.dumps(first_p))}\t{first_p}")
    try:
        p2 = games[game_id]["users"][1]
        send(p2, second_p)
    except Exception as e:
        log(data=f"end_game(), line 71 | {e}",prefix="Err")
        # print(e)
    else:
        log(prefix="SUCCESS", data=f"Sent to {clients[p2]['name']}")
        log(prefix="JSONLOG", data=f"{len(json.dumps(second_p))}\t{second_p}")


def send(client, obj):
    # Sends json object to client
    # Get JSON
    obj_str = json.dumps(obj).encode()
    # Get message length and the OBJ
    data = msg_len(obj_str, 5).encode() + obj_str
    # Send
    client.send(data)


def inactivity_func(time_to_respond, client):
    # Wait X seconds, then check if user has responded.
    start_time = time.time()
    time.sleep(time_to_respond)
    try:
        # Check if user responded
        if clients[client]["last_response"] <= start_time:
            # the user didn't answer
            try:
                kick_from_game(client, f"Received no response for {time_to_respond} seconds. "
                                       f"Kicked for inactivity.")
            except AttributeError as e:  # catches the error that it cannot kick a user from a game if it is not in one
                log(data=f"inactivity_func(), line 90 | {e}", prefix="Err")
                # print(e)
    except KeyError:
        pass

def send_board_update(game_id, seconds=0):
    # Sends the board to both users,
    # along with if it's their turn or not.
    games[game_id]["accepting"] = False
    # delay game
    time.sleep(seconds)
    board = games[game_id]["game"].board
    # FLip board for second player
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
    if not games[game_id]["slow_game"]: #5
        time_to_respond = params["timeout"]

        # if game with cooldown accommodate for lag
        if games[game_id]["cooldown"]:
            time_to_respond += params['delay']
        _thread.start_new_thread(inactivity_func, (time_to_respond, games[game_id]["users"][current_player]))

    try:
        p1 = games[game_id]["users"][0]
        send(p1, first_p)
    except Exception as e:
        # print(e)
        log(data=f"send_board_update(), line 122 | {e}", prefix="Err")
    try:
        p2 = games[game_id]["users"][1]
        send(p2, second_p)
    except Exception as e:
        # print(e)
        log(data=f"send_board_update(), line 122 | {e}", prefix="Err")

    games[game_id]["accepting"] = True

def send_error(user, data, errtype="None"):
    # Send ERROR message to user
    jsonobj = {
        "type": "Error",
        "errtype": errtype,
        "data": data,
    }
    send(user, jsonobj)


def simple_message(user, msgtype, data="", additional_args=None):
    # Generate a simple message JSON and send it
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
    # Add user to game with ID game_id

    if game_id not in games:
        raise KeyError("Invalid game ID")

    # Check if that game is full
    if len(games[game_id]["users"]) == 1:
        games[game_id]["users"].append(user_socket)
        clients[user_socket]["current_game"] = game_id
        send_board_update(game_id)
    # We want to save the game objects of completed games,
    # so we don't allow users to joined deserted lobbies.
    elif len(games[game_id]["users"]) == 0:
        raise IndexError(f"This lobby can't be joined")

    else:
        a, b = [clients[x]["name"] for x in games[game_id]["users"]]
        raise IndexError(f"This game has already began, between {a} and {b}")


def initialize_game(host, is_slow_game=False,delay=False):
    # Initialize a game with 1 host

    game_id = params["game_id"]
    # Add to games dictionary
    games[game_id] = {
        "game": Game(game_id),
        "users": [host],
        "slow_game": is_slow_game,
        "cooldown": delay,
        "next_message": time.time()
    }
    # Set current game of host
    clients[host]["current_game"] = game_id
    # Update next game_id
    params["game_id"] += 1


def matchmaking():
    """
    competition.
    """

    schedule = []  # games schedule
    while 1:
        if len(clients) == 4:
            for client in clients:
                for clnt in clients:
                    if clnt != client:
                        schedule.append([client, clnt])
            break

    while params["serverup"]:

        if len(list(set(competitors))) == 4 and schedule != []:
            # get game id

            # clean competitor's
            [competitors.remove(comp) for comp in competitors]
            match = [0, 0]
            k = 0
            # round competition
            for i in range(2):
                idnum = params["game_id"]
                while match[0] == schedule[k][0] or match[0] == schedule[k][1] or match[1] == schedule[k][1] or match[
                    1] == schedule[k][0]:
                    k += 1

                match = schedule.pop(k)
                k = 0
                clients[match[0]]["current_game"] = idnum
                clients[match[1]]["current_game"] = idnum

                # create game and save it in the games dictionary
                games[idnum] = {
                    "game": Game(idnum),
                    "users": match,
                    "slow_game": False,
                    "next_message": time.time()
                }
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
    if makingmode == "queue":
        # matchmaking_thread = Thread(target=matchmaking, daemon=True)
        # matchmaking_thread.start()
        _thread.start_new_thread(matchmaking, ())

    while params["serverup"]:
        # Accept the user
        client, client_address = SERVER.accept()

        # print(f"{client_address} has connected.")
        log(data=f"{client_address} has connected.", prefix="Login")
        addresses[client] = client_address
        _thread.start_new_thread(handle_client, (client,))

        # Thread(target=handle_client, args=(client,), daemon=True).start()
        # print(f"Starting thread for {client_address}")
        log(data=f"Starting thread for {client_address}", prefix="Login")


def kick_from_game(client, message=None):
    # Kick user from game

    in_game = clients[client]["current_game"]
    if in_game is None:
        raise AttributeError("Cannot kick a user from a game if they're not in one.")
    elif not games[in_game]["game"].game_over:
        # if the user is in a game
        # we need to notify the other player that a user has left.
        clients[client]["current_game"] = None
        name = clients[client]["name"]

        players = list(games[in_game]["users"])

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

        # print(f"{name} has been kicked from lobby #{in_game}")
        log(data=f"{name} has been kicked from lobby #{in_game}", prefix="Kick")

def validate_user_message(client, data, has_logged_in=True):
    # Validate that a user-sent message is valid.
    message_types = ["Login", "Logout", "Lobbies List", "Game Move", "Quit Game", "Join Game", "Start Game", "Restart Game"]
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
    except TypeError:
        send_error(client, errtype="Bad message",
                   data="Invalid Format")
        return False
    if not has_logged_in and msg_type != "Login":
        send_error(client, errtype="Bad Request", data="You have to be logged in first.")
        return False

    if msg_type == "Login":
        if has_logged_in:
            send_error(client, errtype="Bad Request", data="You are already logged in.")
            return False

        if "name" not in data:
            send_error(client, errtype="Bad Message", data="'name' field missing in Login message")
            return False
        elif not isinstance(data["name"], str):
            send_error(client, errtype="Bad Message", data="'name' field needs to be a string")
            return False

    elif msg_type == "Game Move":
        if clients[client]["current_game"] is None:
            return False
        try:
            index = data["index"]
            assert isinstance(index, int)
        except KeyError:
            send_error(client, errtype="Bad Message", data="'index' field missing in Game Move message")
            return False
        except AssertionError:
            send_error(client, errtype="Bad Message", data="'index' field must be int.")
            return False

        # try:
        #     game_id = clients[client]["current_game"]
        #     if games[game_id]["cooldown"]:
        #         send_error(client, "The game is still in cooldown.", errtype="Time Error")
        #         return False
        # except KeyError:
        #     return False

    elif msg_type == "Join Game":
        try:
            game_id = data["game_id"]
            assert isinstance(game_id, int)
        except KeyError:
            send_error(client, errtype="Bad Message", data="'game id' field missing in Join Game message")
            return False
        except AssertionError:
            send_error(client, errtype="Bad Message", data="'game id' field must be int.")
            return False
    elif msg_type == "Start Game":
        if "slow_game" in data:
            if not isinstance(data["slow_game"], bool):
                send_error(client, errtype="Bad Message", data="'slow_game' field needs to be a boolean")
                return False

        if "delay" in data:
            if not isinstance(data["delay"], bool):
                send_error(client, errtype="Bad Message", data="'delay' field needs to be a boolean")
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
        logged_in = False
        name = ""
        # ask for name until you recieve a valid message
        while not logged_in:
            unparsed = client.recv(1024).decode()
            # This was a while True loop making the code afterwards unreachable.
            while not validate_user_message(client, unparsed, has_logged_in=False):
                # added has_logged_in=False, default is True.
                unparsed = client.recv(1024).decode()

            message = json.loads(unparsed)
            name = message["name"]
            taken_names = [x["name"] for x in clients.values()]
            if name in taken_names:
                send_error(client, data=f"This name is already taken. Taken names: {taken_names}", errtype="Invalid Name")
            else:
                send(client,{"type":"Login Successfull"})
                logged_in = True

        print(f"{client}\n has registered as {name}")

    except ConnectionResetError:  # 10054 A
        # print("Client error'd out.")
        log(data=f"Client error'd out. ConnectionResetError handle_client() after 10054 A", prefix="Err")
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
            competitors.append(client)

        name = clients[client]["name"]

        while params["serverup"]:
            try:
                '''
                here we get data from the client
                '''
                buffer = client.recv(1024, MSG_PEEK)
                if buffer != b'':
                    # Maya Vaksin's client is spamming the damn console
                    # print(f"{datetime.now().strftime('%H:%M:%S')} : {clients[client]['name']}: {buffer}")
                    log(data=f"{clients[client]['name']}: {buffer}", prefix="Data")
                unparsed = client.recv(1024)
                valid = validate_user_message(client, unparsed)
                if not valid:
                    continue

                data = json.loads(unparsed)
                log(data=json.dumps(data, indent=4), prefix="JSON")

                msg_type = data["type"]
                # At this point we may assume that we received a valid message from the user.

                if params["matchmaking mode"] == "lobbies":
                    if msg_type == "Start Game":
                        if clients[client]["current_game"]:
                            send_error(client, errtype="Bad Request",
                                       data="You are already in a lobby. To create a new one leave your current one.")
                        else:
                            slow_game, delay = False, False
                            if "slow_game" in data:
                                slow_game = data["slow_game"]
                            if "delay" in data:
                                delay = data["delay"]

                            initialize_game(client, is_slow_game=slow_game, delay=delay)
                            message = f"You have successfully initialized a game with id {params['game_id'] - 1}."

                            if slow_game:
                                message += f"  The game doesn't have a time response limit."

                            if delay:
                                message += f"  The game has a {params['delay']}s delay between each turn."

                            simple_message(client, msgtype="Success",
                                           data=message,
                                           additional_args={"game_id": params['game_id'] - 1})

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

                if msg_type == "Restart Game":
                    if clients[client]["current_game"] is not None:
                        game_id = clients[client]["current_game"]
                        # if user is the owner of the game:
                        # if client != games[game_id]["users"][0]:
                        #     send_error(client, errtype="Permission Error",
                        #                data="You are not the owner of the game. "
                        #                     "Only the owner of the game can restart it.")

                    #
                    if msg_type == "Quit Game":
                        in_game = clients[client]["current_game"]
                        try:
                            kick_from_game(client)
                        except AttributeError:
                            send_error(client, errtype="Bad Request", data="Can't quit game if user is not in a game.")
                        except IndexError:
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully quit game #{in_game}")
                        else:
                            simple_message(client, msgtype="Success",
                                           data=f"You have successfully quit game #{in_game}")

                # #
                # if msg_type == "Game Move":
                #     play_index = data["index"]
                #     try:
                #         game_id = clients[client]["current_game"]

                #         if games[game_id]["accepting"]:
                #             games[game_id]["game"].make_move(play_index, adjust_index=True, verbose=True)
                #         else:
                #             send_error(client, f"The game has a delay of {params['delay']}s between turns. Wait until the delay is over.",
                #                        errtype="Bad Request")
                #             continue

                #         if games[game_id]["game"].game_over:
                #             raise AttributeError

                #     except ValueError:
                #         send_error(client, "You've made an invalid move. It is still your turn.",
                #                    errtype="Invalid Move")
                #     except IndexError as e:
                #         # Selected an empty hole. # GAMEMOVE INDEXERROR
                #         log(prefix="Err", data="User sent bad index, GAMEMOVE INDEXERROR." + f"[{play_index} is empty and thus invalid, it is still your turn.]")
                #         send_error(client, f"{play_index} is empty and thus invalid, it is still your turn.", errtype="Invalid Move")
                #     except TypeError as e:
                #         print(e)
                #         # I don't know what this error is, but it's probably not a non-int value because that's taken care off
                #         # in the validate function in the beginning.

                #         # log(prefix="Err", data="User sent bad value, GAMEMOVE TYPEERROR.")
                #         # send_error(client, "Moves have to be ints. It is still your turn.", errtype="Invalid Move")
                #     except AttributeError:
                #         # Someone won
                #         log(prefix="WON", data=f"Lobby #{clients[client]['current_game']} has ended its game.")
                #         end_game(clients[client]["current_game"])
                #     except KeyError:
                #         """
                #         If the client would send {Game Move} messages while not in a game,
                #         or after being kicked, it would give a KeyError for 
                #         games[clients[client]["current_game"]]["game"]
                #         This is now handled. 
                #         """
                #         send_error(client, "Something went wrong.", errtype="Invalid Move")
                #     else:
                #         cooldown = games[game_id]['cooldown']
                #         clients[client]["last_response"] = time.time()
                #         _thread.start_new_thread(send_board_update, (clients[client]["current_game"], params['delay'] if cooldown else 0))
                #         # send_board_update(clients[client]["current_game"])

            

                #
                if msg_type == "Game Move":
                    if params["matchmaking mode"] == "queue":
                        if time.time() > games[clients[client]["current_game"]]["next_message"]:
                            games[clients[client]["current_game"]]["next_message"] = time.time() + 1
                        else:
                            send_error(client, "You've made a move too soon. It is still in cooldown.",
                                        errtype="Timeout error")
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
                        cooldown = games[game_id]['cooldown']
                        clients[client]["last_response"] = time.time()
                        _thread.start_new_thread(send_board_update, (clients[client]["current_game"], params['delay'] if cooldown else 0))

                        def game_status(game_id):
                            if games[game_id]["game"].winner == 2:
                                return "Tie"
                            users = [get_name(c) for c in games[game_id]["users"]]
                            winner = games[game_id]["game"].winner
                            if winner is None:
                                return "Unfinished"
                            try:
                                return users[winner] + " won."
                            except IndexError:
                                return games[game_id]["game"].winner + " won."

                        for game_id in games:
                            all_lobbies[game_id] = {
                                "users": [get_name(c) for c in games[game_id]['users']],
                                "game status": game_status(game_id)
                            }

                        simple_message(client, msgtype="Notification",
                                        data=f"Here are all of the lobbies. There are currently {params['game_id']} {dynamic}.",
                                        additional_args=all_lobbies)

            except ConnectionResetError:  # 10054 B
                # print(f"{clients[client]['name']} error'd out.")
                log(data=f"{clients[client]['name']} error'd out. ConnectionResetError handle_client after 10054 B ", prefix="Err")
                del addresses[client]
                del clients[client]
                break
            except ConnectionAbortedError as e: # ERR ID ABORT
                # print(f"{clients[client]['name']} error'd out.")
                log(data=f"{clients[client]['name']} error'd out. ConnectionAbortedError handle_client after ERR ID ABORT {e}", prefix="Err")
                del addresses[client]
                del clients[client]
                break
            except UnicodeDecodeError:
                log(prefix="Err", data="User sent bad message, UnicodeDecodeError has occured.")
                send_error(client, errtype="Bad Message", data="UnicodeDecodeError has occured.")
            except KeyError:
                send_error(client, errtype="Internal Error", data="Some player might have disconnected, which might have caused a KeyError.")
            except Exception as e:
                send_error(client, errtype="Server Error", data=str(e))

def broadcast(msg, send_to=None):
    """Broadcasts a message to all the clients."""
    if not send_to:
        send_to = clients
    for sock in send_to:
        try:
            send(sock, msg)
        except ConnectionResetError:  # 10054
            log(data="Client has disconnected", prefix="Err")
            # print("Client has disconnected")


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
