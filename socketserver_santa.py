import socket
import sys
import socketserver

from shared import *
from threading import Lock
import threading

class SantaHandler(socketserver.StreamRequestHandler):
    # Class-level lock to avoid race conditions
    lock = threading.Lock()

    def handle(self):
        global reindeer_counter, elf_counter

        # Read the message
        msg = self.request.recv(MAX_MSG_LEN)

        if b'-' in msg:
            body = msg[msg.index(b'-')+1:]
            msg = msg[:msg.index(b'-')]

        with SantaHandler.lock:
            if msg == MSG_HOLIDAY_OVER:
                # Handle reindeer message
                self.handle_reindeer(body)
            elif msg == MSG_PROBLEM:
                # Handle elf message
                self.handle_elf(body)
            else:
                print(f"Santa received an unknown instruction: {msg}")
                return
        checkin(f"Santa")

    def handle_reindeer(self, body):
        if b'-' in body:
            body = body[body.index(b'-')+1:]
            msg = body[:body.index(b'-')]
            if msg == MSG_HOLIDAY_OVER:
                reindeer_host = body[:body.index(b':')].decode()
                reindeer_port = int(body[body.index(b':')+1:].decode())
                reindeer_counter.append((reindeer_host, reindeer_port))
                if len(reindeer_counter) == num_reindeer:
                    # Deliver presents
                    print(f"Santa is delivering presents with all {num_reindeer} the reindeer")
                    # Tell each reindeer to deliver
                    for host, port in reindeer_counter:
                        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sending_socket.connect((host, port))
                        sending_socket.sendall(MSG_DELIVER_PRESENTS)
                        sending_socket.close()
                    # Reset the reindeer address collection
                    reindeer_counter = []

    def handle_elf(self, body):
        if b'-' in body:
            body = body[body.index(b'-')+1:]
            msg = body[:body.index(b'-')]
            if msg == MSG_PROBLEM:
                elf_host = body[:body.index(b':')].decode()
                elf_port = int(body[body.index(b':')+1:].decode())
                # Append them to a list of collected elf addresses
                elf_counter.append((elf_host, elf_port))
                # If we've collected enough elf addresses, then address their problem
                if len(elf_counter) >= elf_group:
                    # Santa is addressing the elves' problem
                    print(f"Santa is addressing the problem of {elf_group} elves")
                    # Tell each elf that their problem is being addressed
                    for host, port in elf_counter:
                        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sending_socket.connect((host, port))
                        sending_socket.sendall(MSG_SORT_PROBLEM)
                        sending_socket.close()
                    # Reset the elf address collection
                    elf_counter = []

class SantaServer(socketserver.ThreadingTCPServer):
    def __init__(self, server_address, num_reindeer, elf_group, request_handler_class):
        super().__init__(server_address, request_handler_class)
        self.num_reindeer = num_reindeer
        self.elf_group = elf_group
        global reindeer_counter, elf_counter
        reindeer_counter = []
        elf_counter = []

# Rest of the santa function remains the same

# Base santa function, to be called as a process
def santa(host, port, num_reindeer, elf_group):
    with SantaServer((host, port), num_reindeer, elf_group, SantaHandler) as santa_server:
        try:
            # Always be able to handle incoming messages
            santa_server.serve_forever()
        finally:
            # If we keyboard interrupt, this will wrap up all the backend stuff
            santa_server.server_close()

# As an alternative to using the socketserver_santa_problem.py, you may start a 
# standalone santa as described in the handout
if __name__ == "_main_":
    my_host = sys.argv[1]
    my_port = int(sys.argv[2])
    num_reindeer = int(sys.argv[3])
    elf_group = int(sys.argv[4])
    process = Process(target=santa, args=(my_host, my_port, num_reindeer, elf_group))
    process.start()