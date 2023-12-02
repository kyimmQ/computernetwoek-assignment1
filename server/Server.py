import socket
import pickle
import threading
import time
import sys
from server_terminal import *


class Server:
    def __init__(self) -> None:
        self.client = {}
        """
        command_for_client is used for checking whether the server gives a command that need client response,
        because we can only get the response from client in client_handler function, so we can only handle the response
        to that command in the client_handler function.
        """
        self.command_for_client = {
            "client_addr": None,
            "has_command": False,
            "type_of_command": None,
            "data": None,
        }

    def client_handler(self, client_socket, client_addr):
        """listen for client msg"""
        while True:
            try:
                msg = pickle.loads(client_socket.recv(1024))
                """
                if the server sent a command and is waiting response from this client, the response will be
                handled differently.
                """
                if (
                    self.command_for_client["has_command"]
                    and client_addr == self.command_for_client["client_addr"]
                ):
                    self.command_for_client["data"] = msg
                else:
                    msg_list = msg.split()
                    match msg_list[0]:
                        case "fetch":
                            file_name = msg_list[1]
                            client_has_file = []
                            for key in self.client:
                                if file_name in self.client[key][2]:
                                    client_has_file.append(self.client[key][1])
                            # print(file_name, client_has_file)
                            client_socket.send(pickle.dumps(client_has_file))
                        case "publish":
                            self.client[client_addr][2].append(msg_list[1])
                        case "quit":
                            self.client.pop(client_addr)
                            client_socket.close()
                            break
                        case _:
                            continue
            except Exception as e:
                print("client_handler stop!!")
                break

    def command_handler(self, server_socket, my_terminal, root):
        def quit_command():
            my_terminal.insert("end", f"\nClosing server socket!\n>>>")
            my_terminal.mark_set("input", "insert")
            # send msg to clients and close connection
            for addr in self.client:
                self.client[addr][0].send(pickle.dumps("quit"))
                self.client[addr][0].close()
            server_socket.close()

        def ping_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.insert("end", f"\nPinging {client_addr}...\n>>>")
            my_terminal.mark_set("input", "insert")
            client_socket.send(pickle.dumps("ping"))
            # wait for client response in 5s
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.command_for_client["data"]:
                    my_terminal.insert("end", f"\n{client_addr} responded!\n>>>")
                    my_terminal.mark_set("input", "insert")
                    return
            # if client does not response
            my_terminal.insert("end", f"\n{client_addr} is not responding.\n>>>")
            my_terminal.mark_set("input", "insert")
            client_socket.close()
            self.client.pop(client_addr)
            return

        def discover_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.insert("end", f"\nDiscovering {client_addr}...\n>>>")
            my_terminal.mark_set("input", "insert")
            client_socket.send(pickle.dumps("discover"))
            while True:
                if self.command_for_client["data"] is not None:
                    list_of_files = self.command_for_client["data"]
                    break
            self.client[client_addr][2] = list_of_files
            my_terminal.insert("end", f"\nFiles on {client_addr}: {list_of_files}\n>>>")
            my_terminal.mark_set("input", "insert")

        def print_help():
            help_str = """
help - Print all commands and usage
list - List all client with files
ping client_addr - Live check client at client_addr
discover client_addr - Discover files in local repository of client at client_addr
quit - Shut down server socket, use this command before closing the terminal
>>> 
            """
            self.insert("end", f"{help_str}")
            my_terminal.mark_set("input", "insert")

        # get input
        command = my_terminal.get("input", "end")

        self.command_for_client["has_command"] = True
        args_list = command.split()
        print_str = ""
        match args_list[0]:
            case "help":
                if len(args_list) == 1:
                    print_help()
                else:
                    my_terminal.insert(
                        "end",
                        f"\nNot a valid command!\nhelp requires no arguments\n>>>",
                    )
                    my_terminal.mark_set("input", "insert")
            case "list":
                if len(args_list) == 1:
                    i = 1
                    for key in self.client:
                        print_str += f"{i}. {key}: {self.client[key][2]}\n"
                        i += 1
                    my_terminal.insert("end", f"\n{print_str}\n>>>")
                    my_terminal.mark_set("input", "insert")
                else:
                    my_terminal.insert(
                        "end",
                        f"\nNot a valid command!\nlist requires no arguments\n>>>",
                    )
                    my_terminal.mark_set("input", "insert")

            case "ping":
                if len(args_list) == 2:
                    self.command_for_client["type_of_command"] = "ping"
                    client_addr = args_list[1]
                    self.command_for_client["client_addr"] = client_addr
                    if client_addr in self.client:
                        ping_command(client_addr)
                    else:
                        my_terminal.insert("end", f"\nAddress not found!\n>>>")
                        my_terminal.mark_set("input", "insert")
                else:
                    my_terminal.insert(
                        "end", f"\nNot a valid command!\nping requires 1 argument\n>>>"
                    )
                    my_terminal.mark_set("input", "insert")

            case "discover":
                if len(args_list) == 2:
                    self.command_for_client["type_of_command"] = "discover"
                    client_addr = args_list[1]
                    self.command_for_client["client_addr"] = client_addr
                    if client_addr in self.client:
                        discover_command(client_addr)
                    else:
                        my_terminal.insert("end", f"\nAddress not found!\n>>>")
                        my_terminal.mark_set("input", "insert")
                else:
                    my_terminal.insert(
                        "end",
                        f"\nNot a valid command!\ndiscover requires 1 argument\n>>>",
                    )
                    my_terminal.mark_set("input", "insert")

            case "quit":
                if len(args_list) == 1:
                    quit_command()
                    return "break"
                else:
                    my_terminal.insert(
                        "end",
                        f"\nNot a valid command!\nquit requires no arguments\n>>>",
                    )
                    my_terminal.mark_set("input", "insert")
            case _:
                my_terminal.insert("end", f"\nNot a valid command!\n>>>")
                my_terminal.mark_set("input", "insert")

        self.command_for_client = {
            "client_addr": None,
            "has_command": False,
            "type_of_command": None,
            "data": None,
        }
        return "break"

    def client_listener(self, server_socket, my_terminal):
        while True:
            try:
                client_socket, client_addr = server_socket.accept()
                list_of_files = client_socket.recv(1024)
                list_of_files = pickle.loads(list_of_files)
                client_socket.send(pickle.dumps(client_addr))
                my_terminal.insert(
                    "end",
                    f"\nAccepted connection from {client_addr[0]}:{client_addr[1]} with these files: {list_of_files}\n>>>",
                )
                my_terminal.mark_set("input", "insert")
                self.client[f"{client_addr[0]}:{client_addr[1]}"] = [
                    client_socket,
                    client_addr,
                    list_of_files,
                ]
                # new thread for handling that client
                threading.Thread(
                    target=self.client_handler,
                    args=[client_socket, f"{client_addr[0]}:{client_addr[1]}"],
                ).start()
            except Exception as e:
                my_terminal.insert("end", f"\nclient_listener stop!!\n>>>")
                my_terminal.mark_set("input", "insert")
                return

    def main(self):
        # creating & handling server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = "10.128.84.222"
        server_port = 65432
        server_socket.bind((server_ip, server_port))
        server_socket.listen(5)
        # creating terminal
        root = tk.Tk()
        root.title("Server terminal")
        my_terminal = ConsoleText(
            root, bg="black", fg="white", insertbackground="white"
        )
        my_terminal.bind(
            "<Return>",
            lambda event, server_socket=server_socket, my_terminal=my_terminal, root=root: self.command_handler(
                server_socket, my_terminal, root
            ),
        )
        my_terminal.pack(fill=tk.BOTH, expand=True)
        my_terminal.insert("end", f"\nListening on {server_ip}:{server_port}\n>>>")
        my_terminal.mark_set("input", "insert")

        # listen for client
        threading.Thread(
            target=self.client_listener, args=[server_socket, my_terminal]
        ).start()

        # terminal loop
        root.mainloop()


if __name__ == "__main__":
    (Server()).main()
