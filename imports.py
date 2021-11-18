# imports were put here to remove all the imports from server.py and client.py
# SERVER AND CLIENT
from threading import Thread, Event
from socket import AF_INET, socket, SOCK_STREAM, MSG_PEEK, gethostname, gethostbyname
import json
from re import search, sub
import time
from datetime import datetime

# CLIENT
import random

# SERVER
import mancala
from mancala import Mancala as Game
