import socket
import sys
import socketserver

from shared import *
from threading import Lock

class PorchHandler(socketserver.StreamRequestHandler):
    def handle(self):
        global elf_counter

        msg = self.request.recv(MAX_MSG_LEN).decode()
        elf_info = msg.split('-')
        elf_address = elf_info[1]

        with self.server.elf_lock:
            elf_counter.append(elf_address)
            print(f"Received message from elf {elf_info[0]}. Total count in group: {len(elf_counter)}")

            if len(elf_counter) >= self.server.elf_group:
                print("Enough elves have assembled. Notifying the first elf to notify Santa.")
                first_elf_address = elf_counter[0]
                try:
                    notify_first_elf_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    first_elf_host, first_elf_port = first_elf_address.split(':')
                    notify_first_elf_socket.connect((first_elf_host, int(first_elf_port)))
                    notify_first_elf_socket.sendall("notify_santa".encode())
                except Exception as e:
                    print(f"Error notifying first elf: {e}")
                finally:
                    notify_first_elf_socket.close()

                for elf_addr in elf_counter[1:]:
                    try:
                        notify_elf_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        elf_host, elf_port = elf_addr.split(':')
                        notify_elf_socket.connect((elf_host, int(elf_port)))
                        notify_elf_socket.sendall("group_ready".encode())
                    except Exception as e:
                        print(f"Error notifying elf: {e}")
                    finally:
                        notify_elf_socket.close()

                elf_counter = []




# A socketserver class to run the porch as a constant server
class PorchServer(socketserver.ThreadingTCPServer):
    # Constructor for our custom class. If we wish to add more variables or
    # arguments this is where we could do it
    def __init__(self, server_address, elf_group, santa_host, santa_port, request_handler_class):
        # Call the parent classes constructor
        super().__init__(server_address, request_handler_class)
        # Record the expected number of elves, and santas address
        self.elf_group = elf_group
        self.santa_host = santa_host
        self.santa_port = santa_port
        # Setup the list for collecting elf addresses
        self.elf_counter = []
        # Setup lock for accessing shared list
        self.elf_lock = Lock()
        global elf_counter
        elf_counter = []
 
# Base porch function, to be called as a process
def porch(my_host, my_port, santa_host, santa_port, elf_group):
    # Start a socketserver to always be listening
    with PorchServer((my_host, my_port), elf_group, santa_host, santa_port, PorchHandler) as porch_server:
        try:
            # Always be able to handle incoming messages
            porch_server.serve_forever()
        finally:
            # If we keyboard interupt this will wrap up all the backend stuff
            porch_server.server_close()

# As an alternative to using the true_santa_problem.py, you may start a 
# standalone porch as described in the handout
if __name__ == "__main__":
    process = Process(target=porch, args=(sys.argv[1:]))
    process.start()