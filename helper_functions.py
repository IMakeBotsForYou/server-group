from threading import Thread, Event
import time
# put here to remove all the imports from server.py and client.py
from socket import AF_INET, socket, SOCK_STREAM, MSG_PEEK, gethostname, gethostbyname
from re import search
import json

colours = {
    "red": "dd0404",
    "pink": "ff6666",
    "low-yellow": "d9c000",
    "orange-warning": "D49B00",
    "low-green": "339966",
    "bright-green": "27DB03",
    "blue": "0066cc",
    "whisper-gray": "ab9aa0",
    "white": "FFFFFF"
}


def join_all(threads, timeout):
    """
    Args:
        threads: a list of thread objects to join
        timeout: the maximum time to wait for the threads to finish
    Raises:
        RuntimeError: is not all the threads have finished by the timeout
    :return Amount of threads who were still active
    """
    start = cur_time = time.time()
    while cur_time <= (start + timeout):
        for thread in threads:
            if thread.is_alive():
                thread.join(timeout=0)
        if all(not t.is_alive() for t in threads):
            break
        time.sleep(0.1)
        cur_time = time.time()
    else:
        print(f"Force timeout after {timeout} seconds | ", end="  ")
        return len([t for t in threads if t.is_alive()])


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


def encode(txt, key):
    """
    :param txt: text to encrypt
    :param key: XOR key
    :return: Encrypted text
    """
    return ''.join([chr(ord(a) ^ key) for a in txt])


def call_repeatedly(interval, func, *args):
    """
    Used to check if the user hasn't talked for X seconds.

    :param interval: The interval between the checks
    :param func: Function to run at said interval
    :param args: Arguments for command
    :return: When called, stops the looping.
    """
    stopped = Event()

    def loop():
        x = "continue"
        while not stopped.wait(interval) or x == "stop":  # the first call is in `interval` secs
            x = func(*args)  # if loop asks to stop, stop it

    Thread(target=loop).start()
    return stopped.set
