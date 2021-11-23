from imports import *


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


def pretty_print_log(log):
    # Pretty print log (optional)
    for num, data in log.items():
        special = data['special event']
        special = f'\t| {special}' if special != 'nothing' else ''
        print(f"{num}: {data['player']} played {data['move']}{special}")


def move(server):
    # Make random move
    index = random.randint(1, 6)
    print(f"--Making move {index}--")

    # Send Game Move message to server
    server.send(
        json.dumps({
            "type": "Game Move",
            "index": index
        }).encode()
    )


def send_data(server):
    while 1:
        # Choose command
        command = input().lower().strip()
        # The command 'Start Game' can be accessed by the aliases 'start' or 'create'.
        # The rest of the command work in the same way.
        # Create a game
        if command in ["start", "create"]:

            server.send(json.dumps(
                {
                    "type": "Start Game",
                    "slow_game": input('Slow Game? > ') == 't',        # Have a timeout that forces a kick if there's no response after X seconds.
                    "delay": input('Delay Between Turns? > ') == 't'   # Delay between each turn, so the game can be seen in real time.
                }
            ).encode())

        # Restart a lobby
        elif command in ["restart", "reset"]:
            server.send(json.dumps(
                {
                    "type": "Restart Game"
                }).encode())

        # Join a lobby by ID
        elif command == "join":
            server.send(json.dumps(
                {
                    "type": "Join Game",
                    "game_id": int(input("ID > "))
                }).encode())

        # Leave a lobby
        elif command in ["quit", "leave"]:
            server.send(json.dumps(
                {
                    "type": "Quit Game"
                }).encode())

        # Register a name in the server
        elif command in ["login"]:
            server.send(json.dumps(
                {
                    "type": "Login", "name": input("Name > ")
                }).encode())

        # Leave server (optional, if you close the client it leaves)
        elif command in ["logout"]:
            server.send(json.dumps(
                {
                    "type": "Logout"
                }).encode())

        # Show all lobbies
        elif command in ["list", "lobbies", "showall"]:
            server.send(json.dumps(
                {
                    "type": "Lobbies List"
                }).encode())

        else:
            # If command not in those commands, send raw text.
            server.send(command.encode())


def recv_data(server):
    while 1:
        # Print the socket buffer
        # log(data=server.recv(1024 * 10, MSG_PEEK), prefix="Data")

        # Get message length
        msg_length = int(server.recv(5))

        # Receive message
        data = json.loads(server.recv(msg_length))
        # Print the JSON
        log(data=json.dumps(data, indent=4), prefix="JSON")
        print()

        # If we received board update
        if data["type"] == "Board Update":
            if data["your turn"]:
                move(server)
            log(data=data["board"])

        # If we got an error
        elif data["type"] == "Error":

            if data["errtype"] == "Invalid Name":
                log(data=data["data"], prefix="Error")

            if data["errtype"] == "Invalid Move":
                log(data=data["data"], prefix="Error")
                move(server)

        # Game over message (includes log)
        elif data["type"] == "Game Over":
            wewon = data["won"]
            # log(data=data["log"], prefix="Game Log")
            pretty_print_log(data["log"])
            # sock.send(json.dumps({"type": "Restart Game"}).encode())


if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    ip = "localhost"
    port = int(open("port.txt").read())
    sock.connect((ip, port))

    # Receive thread
    recv_thread = Thread(target=lambda: recv_data(sock))
    recv_thread.start()

    # Send data to server thread
    send_thread = Thread(target=lambda: send_data(sock))
    send_thread.start()

    send_thread.join()
    recv_thread.join()
