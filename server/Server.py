import socket
import os
import pickle
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import sys
sys.path.append('../')
from console_text_redirector import ConsoleTextRedirector

class ConsoleAppServer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Transfer Server")
        self.geometry("600x400")

        label_app = tk.Label(self, text="File-sharing application", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_app.pack(side=tk.TOP, pady=10)
        label_side = tk.Label(self, text="Server side", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_side.pack(side=tk.TOP)

        button_frame = tk.Frame(self, bg="#D0D0D0")
        button_frame.pack(side=tk.TOP, fill=tk.X)

        button_list = tk.Button(button_frame, text="List", command=self.button_list_action, bg="#90EE90")
        button_list.grid(row=0, column=0, padx=5, pady=5)

        button_help = tk.Button(button_frame, text="Help", command=self.button_help_action, bg="#90EE90")
        button_help.grid(row=0, column=1, padx=5, pady=5)

        button_discover = tk.Button(button_frame, text="Discover", command=self.button_discover_action, bg="#FFD700")
        button_discover.grid(row=1, column=0, padx=5, pady=5)
        self.entry_discover = tk.Entry(button_frame)
        self.entry_discover.grid(row=1, column=1, padx=5, pady=5)

        button_ping = tk.Button(button_frame, text="Ping", command=self.button_ping_action, bg="#FFD700")
        button_ping.grid(row=2, column=0, padx=5, pady=5)
        self.entry_ping = tk.Entry(button_frame)
        self.entry_ping.grid(row=2, column=1, padx=5, pady=5)

        console_frame = tk.Frame(self, bg="#F0F0F0")
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Arial", 12), bg="#F0F0F0", fg="#333333")  # Dark gray text on light gray background
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.console_text.insert(tk.END, ''' Welcome to file transferring application! 
 This is the SERVER side!
''')

        sys.stdout = ConsoleTextRedirector(self.console_text)

        self.console_text.tag_configure("red", foreground="red")
        self.console_text.tag_configure("blue", foreground="blue")
        self.console_text.tag_configure("black", foreground="black")

    def button_help_action(self):
        # self.print_with_color(">>> ", "black")
        self.print_with_color("Help\n", "blue")
        print('''list - List all client with files
ping client_addr - Live check client at client_addr
discover client_addr - Discover files in local repository of client at client_addr
quit - Shut down server socket, use this command before closing the terminal
''')
        self.console_text.mark_set('insert', 'end')
        
    def button_list_action(self):
        # self.print_with_color(">>> ", "black")
        self.print_with_color("list", "blue")
        self.console_text.mark_set('insert', 'end')

    def button_discover_action(self):
        entry_discover_text = self.entry_discover.get()
        if entry_discover_text == "":
            # self.print_with_color(">>> ", "black")
            self.print_with_color("discover: Please enter a client_address!\n", "red")
            self.console_text.mark_set('insert', 'end')
        else:
            self.print_with_color("discover " + entry_discover_text, "blue")
            self.console_text.mark_set('insert', 'end')

    def button_ping_action(self):
        entry_ping_text = self.entry_ping.get()
        if entry_ping_text == "":
            # self.print_with_color(">>> ", "black")
            self.print_with_color("ping: Please enter a client_address!\n", "red")
            self.console_text.mark_set('insert', 'end')
        else:
            self.print_with_color("ping " + entry_ping_text, "blue")
            self.console_text.mark_set('insert', 'end')

    def print_with_color(self, msg, color: str):
        self.console_text.insert(tk.END, msg, color)
        self.console_text.see(tk.END)
        self.console_text.mark_set('insert', 'end')


class Server:
    def __init__(self) -> None:
        self.client = {}
        self.command_for_client = {
            "client_addr": None,
            "has_command": False,
            "type_of_command": None,
            "data": None,
        }

    def client_handler(self, client_socket, client_addr):
        while True:
            try:
                msg = pickle.loads(client_socket.recv(1024))
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

    def command_handler(self, server_socket, my_terminal):
        def quit_command():
            my_terminal.console_text.insert("end", f"Closing server socket!\n\n")
            my_terminal.console_text.mark_set("input", "insert")
            for addr in self.client:
                self.client[addr][0].send(pickle.dumps("quit"))
                self.client[addr][0].close()
            server_socket.close()

        def ping_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.console_text.insert("end", f"Pinging {client_addr}...\n")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.send(pickle.dumps("ping"))
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.command_for_client["data"]:
                    my_terminal.console_text.insert("end", f"{client_addr} responded!\n\n")
                    my_terminal.console_text.mark_set("input", "insert")
                    return
            my_terminal.console_text.insert("end", f"{client_addr} is not responding.\n\n")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.close()
            self.client.pop(client_addr)
            return

        def discover_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.console_text.insert("end", f"Discovering {client_addr}...\n")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.send(pickle.dumps("discover"))
            while True:
                if self.command_for_client["data"] is not None:
                    list_of_files = self.command_for_client["data"]
                    break
            self.client[client_addr][2] = list_of_files
            my_terminal.console_text.insert("end", f"Files on {client_addr}: {list_of_files}\n\n")
            my_terminal.console_text.mark_set("input", "insert")


        command = my_terminal.console_text.get("end-2l", "end-1c")
        start_index = next((i for i, char in enumerate(command) if char.isalpha()), None)
        if start_index is not None:
            command = command[start_index:]
        # print(str(command))
        
        self.command_for_client["has_command"] = True
        args_list = command.split()
        print_str = ""
        match args_list[0]:
            case "list":
                if len(args_list) == 1:
                    i = 1
                    for key in self.client:
                        print_str += f"{i}. {key}: {self.client[key][2]}\n"
                        i += 1
                    my_terminal.console_text.insert("end", f"{print_str}\n")
                    my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"Not a valid command!\nlist requires no arguments\n",
                    )
                    my_terminal.console_text.mark_set("input", "insert")

            case "ping":
                if len(args_list) == 2:
                    self.command_for_client["type_of_command"] = "ping"
                    client_addr = args_list[1]
                    self.command_for_client["client_addr"] = client_addr
                    if client_addr in self.client:
                        ping_command(client_addr)
                    else:
                        my_terminal.console_text.insert("end", f"Address not found!\n\n")
                        my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end", f"Not a valid command!\nping requires 1 argument\n\n"
                    )
                    my_terminal.console_text.mark_set("input", "insert")

            case "discover":
                if len(args_list) == 2:
                    self.command_for_client["type_of_command"] = "discover"
                    client_addr = args_list[1]
                    self.command_for_client["client_addr"] = client_addr
                    if client_addr in self.client:
                        discover_command(client_addr)
                    else:
                        my_terminal.console_text.insert("end", f"Address not found!\n\n")
                        my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"Not a valid command!\ndiscover requires 1 argument\n\n",
                    )
                    my_terminal.console_text.mark_set("input", "insert")

            case "quit":
                if len(args_list) == 1:
                    quit_command()
                    return "break"
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"Not a valid command!\nquit requires no arguments\n\n",
                    )
                    my_terminal.console_text.mark_set("input", "insert")
            case _:
                my_terminal.console_text.insert("end", f"Not a valid command!\n\n")
                my_terminal.console_text.mark_set("input", "insert")

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
                my_terminal.console_text.insert(
                    "end",
                    f"Accepted connection from {client_addr[0]}:{client_addr[1]} with these files: {list_of_files}\n\n",
                )
                my_terminal.console_text.mark_set("input", "insert")
                self.client[f"{client_addr[0]}:{client_addr[1]}"] = [
                    client_socket,
                    client_addr,
                    list_of_files,
                ]
                threading.Thread(
                    target=self.client_handler,
                    args=[client_socket, f"{client_addr[0]}:{client_addr[1]}"],
                ).start()
            except Exception as e:
                my_terminal.console_text.insert("end", f"client_listener stop!!\n\n")
                my_terminal.console_text.mark_set("input", "insert")
                return

    def main(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = ""
        with open('Server_IP.txt', 'r') as file:
            server_ip = file.read().strip()
        server_port = 65432
        server_socket.bind((server_ip, server_port))
        server_socket.listen(5)

        my_terminal = ConsoleAppServer()
        my_terminal.title("Server terminal")
        my_terminal.bind(
            "<Return>",
            lambda event, server_socket=server_socket, my_terminal=my_terminal: self.command_handler(
                server_socket, my_terminal
            ),
        )
        my_terminal.console_text.insert("end", f"Listening on {server_ip}:{server_port}\n\n")
        my_terminal.console_text.mark_set("input", "insert")

        threading.Thread(
            target=self.client_listener, args=[server_socket, my_terminal]
        ).start()

        my_terminal.mainloop()


if __name__ == "__main__":
    (Server()).main()
