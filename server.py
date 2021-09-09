"""Server for multi-threaded (asynchronous) chat application."""
from helper_functions import *

# global parameters
parms = {
    "verbose": True,
    "serverup": True,
    "timeout": 5  # 5 seconds
}


def format_message(msg_type, data):
    try:
        return msg_type+msg_len(data.encode())+data
    except:
        return msg_type+msg_len(data)+data


def accept_incoming_connections():
    """
    First checks if a connection is a server-scanner or a client.
    If it's a user, it accepts the connection and sends them a welcome message.
    Then, we start a thread for that user and handle their input.
    """
    while parms["serverup"]:
        # Accept the user
        client, client_address = SERVER.accept()

        print(f"{client_address} has connected.")
        addresses[client] = client_address
        Thread(target=handle_client, args=(client,)).start()
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
        if current_time - clients[client]["last_response"] > parms["timeout"]:
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
        name = client.recv(1024).decode()
        # if there's any keywords we want to ban
        # this might be useful if we have reserved keywords for system functions, like @ or !
        banned_words = []
        names = [x[0] for x in clients.values()]

        banned_words_used = [key_word for key_word in banned_words if name.find(key_word) != -1]
        banned_words_used += [x for x in names if name == x]
        while len(banned_words_used) != 0 or (len(name) > 16 or len(name) < 3):
            if len(name) > 16 or len(name) < 3:
                data = "Name must be between 3-16 characters"
                # 3-Length 6-Color 1-Display || Data
                header = msg_len(data)
                client.send((header + data).encode())
            else:
                data = "Invalid nickname, the name is either taken\nor it has an illegal character"
                # 3-Length 6-Color 1-Display || Data
                header = msg_len(data)
                client.send((header + data).encode())
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
                           "ping_function": call_repeatedly(60, inactivity_check, client)}

        while parms["serverup"]:
            # here we get data from the client
            pass


def broadcast(msg, send_to=None):
    """Broadcasts a message to all the clients."""
    if not send_to:
        send_to = clients
    for sock in send_to:
        try:
            sock.send(msg.encode())
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
