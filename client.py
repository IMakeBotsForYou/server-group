from imports import *


def log(data, prefix=None):
    if prefix is None:
        prefix = "Log"
    current_time = datetime.now().strftime("%H:%M:%S")
    print(f"[{prefix}]\t{current_time}  {data}")


def pretty_print_log(log):
    for num, data in log.items():
        special = data['special event']
        special = f'\t| {special}' if special != 'nothing' else ''
        print(f"{num}: {data['player']} played {data['move']}{special}")


def move(server):
    index = random.randint(1, 6)
    print(f"--Making move {index}--")
    server.send(
        json.dumps({
            "type": "Game Move",
            "index": index
        }).encode()
    )


def send_data(server):
    while 1:
        fullcommand = input().lower()
        if len(fullcommand.split(" ")) == 0:
            continue
        command = fullcommand.split(" ")[0]
        args = [arg.strip(' \t\n\r') for arg in fullcommand.split(" ")][1:]

        if command in ["start", "create"]:
            slow, delay = False, False
            try:
                slow, delay = args[:2]  # there might be more args we don't care about.
            except:
                if len(args) == 1:
                    delay = False
                elif len(args) == 0:
                    slow, delay = False, False

            slow = True if slow == 't' else False
            delay = True if delay == 't' else False
            server.send(json.dumps({"type": "Start Game", "slow_game": slow, "delay": delay}).encode())

        elif command in ["restart", "reset"]:
            server.send(json.dumps({"type": "Restart Game"}).encode())
        elif command == "join":
            server.send(json.dumps({"type": "Join Game", "game_id": int(input("ID > "))}).encode())
        elif command in ["quit", "leave"]:
            server.send(json.dumps({"type": "Quit Game"}).encode())
        elif command in ["login"]:
            server.send(json.dumps({"type": "Login", "name": input("Name > ")}).encode())
        elif command in ["logout"]:
            server.send(json.dumps({"type": "Logout"}).encode())
        elif command in ["list", "lobbies", "showall"]:
            server.send(json.dumps({"type": "Lobbies List"}).encode())

        else:
            server.send(command.encode())


def recv_data(server):
    while 1:
        log(data=server.recv(1024 * 10, MSG_PEEK), prefix="Data")
        msg_length = int(server.recv(5))
        data = json.loads(server.recv(msg_length))
        log(data=json.dumps(data, indent=4), prefix="JSON")
        print()
        if data["type"] == "Board Update":
            if data["your turn"]:
                move(server)
            log(data=data["board"])

        elif data["type"] == "Error":

            if data["errtype"] == "Invalid Name":
                log(data=data["data"], prefix="Error")

            if data["errtype"] == "Invalid Move":
                log(data=data["data"], prefix="Error")
                move(server)

        # elif data["type"] == "Welcome":
        #     server.send(input().encode())

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
    recv_thread = Thread(target=lambda: recv_data(sock))
    recv_thread.start()
    send_thread = Thread(target=lambda: send_data(sock))
    send_thread.start()
    send_thread.join()
    recv_thread.join()
