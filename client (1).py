import random
import json
from threading import Thread
from socket import AF_INET, socket, SOCK_STREAM, MSG_PEEK


def move(server):
    server.send(
        json.dumps({
            "type": "Game Move",
            "index": random.randint(1, 6)
        }).encode()
    )


def send_data(server):
    while 1:
        command = input("> ").lower()
        if command in ["start", "create"]:
            server.send(json.dumps({"type": "Start Game"}).encode())
        elif command in ["restart", "reset"]:
            server.send(json.dumps({"type": "Restart Game"}).encode())
        elif command == "join":
            server.send(json.dumps({"type": "Join Game", "game_id": int(input("ID > "))}).encode())
        elif command in ["quit", "leave"]:
            server.send(json.dumps({"type": "Quit Game"}).encode())
        else:
            server.send(command.encode())


def recv_data(server):
    while 1:
        print(server.recv(1024*10, MSG_PEEK))
        msg_length = int(server.recv(5))
        data = json.loads(server.recv(msg_length))
        if data["type"] == "Board Update":
            if data["your turn"]:
                move(server)

        elif data["type"] == "error":

            if data["errtype"] == "Invalid Name":
                print(data["data"])
                server.send(input("New name > ").encode())

            if data["errtype"] == "Invalid Move":
                move(server)
                pass

        # elif data["type"] == "Welcome":
        #     server.send(input().encode())

        elif data["type"] == "Game Over":
            print(data["log"])
            # if wewon:
            #     sock.send(json.dumps({"type": "Restart Game"}).encode())


if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    ip = "10.0.0.12"
    port = int(open("port.txt").read())
    sock.connect((ip, port))
    recv_thread = Thread(target=lambda: recv_data(sock))
    recv_thread.start()
    send_thread = Thread(target=lambda: send_data(sock))
    send_thread.start()
    send_thread.join()

