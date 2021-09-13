import random

from helper_functions import *


def move(server):
    server.send(
        json.dumps({
            "type": "Game Move",
            "index": random.randint(1, 6)
        }).encode()
    )


def recv_data(server):
    while 1:
        data = json.loads(server.recv(1024*10))
        if data["type"] == "board update":
            if data["your turn"]:
                move(server)
            print(data["board"])

        elif data["type"] == "error":
            move(server)

        elif data["type"] == "Welcome":
            server.send(input().encode())
        elif data["type"] == "Game Over":
            wewon = data["won"]
            print(wewon)
            print(data["log"])
            break
        else:
            print(json.dumps(data, indent=2))


if __name__ == '__main__':
    sock = socket(AF_INET, SOCK_STREAM)
    ip = "10.0.0.12"
    port = int(open("port.txt").read())
    sock.connect((ip, port))

    recv_thread = Thread(target=lambda: recv_data(sock))
    recv_thread.start()
    recv_thread.join()

