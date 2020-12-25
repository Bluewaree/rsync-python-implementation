import socket
from _thread import *
import threading
import sys

from server.handlers import client_handler


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    HOST, PORT = "localhost", 9999
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(5)
    print("socket is listening")
    while True:
        c, addr = s.accept()
        print('Connected to :', addr[0], ':', addr[1])
        start_new_thread(client_handler, (c, path))
    s.close()
