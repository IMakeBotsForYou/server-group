"""Server for multi-threaded (asynchronous) chat application."""
import mankala
from mankala import Mankala as Game

from helper_functions import *

# global parameters
params = {
    "gameid": 0,
    "verbose": True,
    "serverup": True,
    "timeout": 5  # 5 seconds
}

queue = []
games = {

}
game_logs = {

}


def end_game(game_id):
    game = games[game_id]["game"]
    winner = game.winner
    first_p = {
        "type": "End Game",
        "won": winner == 0,
        "log": game.log
    }
    second_p = {
        "type": "End Game",
        "won": winner == 1,
        "log": game.log
    }
    p1, p2 = games[game_id]["users"]
    p1.send(json.dumps(first_p).encode())
    p2.send(json.dumps(second_p).encode())


def send_board_update(game_id):
    board = games[game_id]["game"].board
    flipped_board = mankala.flip_board(board)
    current_turn = games[game_id]["game"].current_player

    first_p = {
        "type": "board update",
        "board": board,
        "your turn": current_turn == 0
    }
    second_p = {
        "type": "board update",
        "board": flipped_board,
        "your turn": current_turn == 1
    }
    p1, p2 = games[game_id]["users"]
    p1.send(json.dumps(first_p).encode())
    p2.send(json.dumps(second_p).encode())


def send_error(user, data, errtype=None):
    jsonobj = {
        "type": "error",
        "errtype": errtype,
        "data": data,
    }
    user.send(json.dumps(jsonobj).encode())


def matchmaking():
    while 1:
        if len(queue) > 1:
            # get game id
            idnum = params["gameid"]

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
            params["gameid"] += 1
            # notify the 2 users of game start.
            # first user to join the queue gets first move.
            send_board_update(idnum)


def accept_incoming_connections():
    """
    First checks if a connection is a server-scanner or a client.
    If it's a user, it accepts the connection and sends them a welcome message.
    Then, we start a thread for that user and handle their input.
    """
    matchmaking_thread = Thread(target=matchmaking, daemon=True)
    matchmaking_thread.start()
    while params["serverup"]:
        # Accept the user
        client, client_address = SERVER.accept()

        print(f"{client_address} has connected.")
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,), daemon=True).start()
        print(f"Starting thread for {client_address}")


def inactivity_check(client):
    """
    Checks the time between the user's last message and now,
    if over the specified time, send a message.
    :param client: client being checked
    :return: None
    """
    current_time = int(time.time())
    try:
        if current_time - clients[client]["last_response"] > params["timeout"]:
            clients[client]["last_response"] = int(time.time())
            # kick(client)
            # print(clients[client]["name"])
    except KeyError:
        # If there's an error then stop looping this
        return "stop"


def handle_client(client):  # Takes client socket as argument.
    """
    Handles a single client connection.
    This is done by first registering a valid name.
    Then we handle every message, from normal, Commands everyone can see,
    and commands only the user can see.
    """
    try:
        m = json.dumps({"type": "Welcome", "data": "Choose a name!"}).encode()
        client.send(m)
        name = client.recv(1024).decode()
        # if there's any keywords we want to ban
        # this might be useful if we have reserved keywords for system functions, like @ or !
        banned_words = []
        names = [x["name"] for x in clients.values()]

        banned_words_used = [key_word for key_word in banned_words if name.find(key_word) != -1]
        banned_words_used += [x for x in names if name == x]
        while len(banned_words_used) != 0 or (len(name) > 16 or len(name) < 3):

            if len(name) > 16 or len(name) < 3:
                data = "Name must be between 3-16 characters"
            else:
                data = "Invalid nickname, the name is either taken\nor it has an illegal character"

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
                           "last_response": int(time.time()),
                           "games": {
                               "wins": 0,
                               "loses": 0
                           },
                           "current game": None,
                           "ping_function": call_repeatedly(60, inactivity_check, client)}

        queue.append(client)

        while params["serverup"]:

            '''
            here we get data from the client
            '''
            data = json.loads(client.recv(1024))
            msg_type = data["type"]
            if msg_type == "Game Move":
                play_index = data["index"]
                try:
                    games[clients[client]["current game"]]["game"].make_move(play_index, adjust_index=True)
                except ValueError:
                    send_error(client, "You've made an invalid move. It is still your turn.", errtype="Invalid Move")
                except IndexError as e:
                    # Selected an empty hole.
                    send_error(client, str(e) + " It is still your turn.", errtype="Invalid Move")
                except AttributeError:
                    #Someone won
                    end_game(clients[client]["current game"])

                else:
                    send_board_update(clients[client]["current game"])


def broadcast(msg, send_to=None):
    """Broadcasts a message to all the clients."""
    if not send_to:
        send_to = clients
    for sock in send_to:
        try:
            sock.send(msg.encode())
        except AttributeError:
            sock.send(msg)
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
