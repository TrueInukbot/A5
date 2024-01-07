import socket
import sys
import socketserver

from shared import *
from threading import Lock

# A handler function, called on each incoming message to the server
class StableHandler(socketserver.StreamRequestHandler):
    def handle(self):
        global reindeer_count
        global reindeer_addresses

        msg = self.request.recv(MAX_MSG_LEN).decode()
        reindeer_info = msg.split('-')
        reindeer_address = reindeer_info[1]
        reindeer_count += 1
        reindeer_addresses.append(reindeer_address)

        print(f"Received message from reindeer. Total count: {reindeer_count}")

        if reindeer_count == self.server.num_reindeer:
            print("All reindeer have returned. Notifying the last one.")
            last_reindeer_address = reindeer_addresses[-1]
            notify_last_reindeer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            last_reindeer_host, last_reindeer_port = last_reindeer_address.split(':')
            notify_last_reindeer_socket.connect((last_reindeer_host, int(last_reindeer_port)))
            message = f"last-{'-'.join(reindeer_addresses)}-{self.server.santa_host}:{self.server.santa_port}"
            notify_last_reindeer_socket.sendall(message.encode())
            notify_last_reindeer_socket.close()
            reindeer_count = 0
            reindeer_addresses = []

# A socketserver class to run the stable as a constant server
class StableServer(socketserver.ThreadingTCPServer):
    # Constructor for our custom class. If we wish to add more variables or
    # arguments this is where we could do it
    def __init__(self, server_address, num_reindeer, santa_host, santa_port, request_handler_class):
        # Call the parent classes constructor
        super().__init__(server_address, request_handler_class)
        # Record the expected number of reindeer, and santas address
        self.num_reindeer = num_reindeer
        self.santa_host = santa_host
        self.santa_port = santa_port
        global reindeer_count
        global reindeer_addresses
        reindeer_count = 0
        reindeer_addresses = [] 
# Base stable function, to be called as a process
def stable(my_host, my_port, santa_host, santa_port, num_reindeer):
    # Start a socketserver to always be listening
    with StableServer((my_host, my_port), num_reindeer, santa_host, santa_port, StableHandler) as stable_server:
        try:
            # Always be able to handle incoming messages
            stable_server.serve_forever()
        finally:
            # If we keyboard interupt this will wrap up all the backend stuff
            stable_server.server_close()

# As an alternative to using the socketserver_santa_problem.py, you may start a 
# standalone elf as described in the handout
if __name__ == "__main__":
    process = Process(target=stable, args=(sys.argv[1:]))
    process.start()