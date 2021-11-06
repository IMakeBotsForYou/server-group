from threading import Thread, Event
import time
# put here to remove all the imports from server.py and client.py
from socket import AF_INET, socket, SOCK_STREAM, MSG_PEEK, gethostname, gethostbyname
from re import search
import json
import random
