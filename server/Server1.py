import socket
import pickle
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import sys

class ConsoleApp(tk.Tk):
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

        button1 = tk.Button(button_frame, text="Discover", command=self.button_discover_action, bg="#FFD700")
        button1.grid(row=1, column=0, padx=5, pady=5)
        self.entry1 = tk.Entry(button_frame)
        self.entry1.grid(row=1, column=1, padx=5, pady=5)

        button2 = tk.Button(button_frame, text="Ping", command=self.button_ping_action, bg="#FFD700")
        button2.grid(row=2, column=0, padx=5, pady=5)
        self.entry2 = tk.Entry(button_frame)
        self.entry2.grid(row=2, column=1, padx=5, pady=5)

        console_frame = tk.Frame(self, bg="#F0F0F0")  # Light gray background for the console frame
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Arial", 12), bg="#F0F0F0", fg="#333333")  # Dark gray text on light gray background
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.console_text.insert(tk.END, ''' Welcome to file transferring application! 
 This is the SERVER side!
''')

        sys.stdout = ConsoleTextRedirector(self.console_text)

        self.console_text.tag_configure("red", foreground="red")
        self.console_text.tag_configure("blue", foreground="blue")

        self.console_text.bind("<Control-c>", self.copy)
        self.console_text.bind("<Control-v>", self.paste)

    def button_help_action(self):
        print(">>>", end=" ")
        self.print_with_color("Help\n", "blue")
        print('''List - List all clients with files
 Ping client_addr - Live check client at client_addr
 Discover client_addr - Discover files in the local repository of the client at client_addr
''')
        
    def button_list_action(self):
        print(">>>", end=" ")
        self.print_with_color("list", "blue")

    def button_discover_action(self):
        entry1_text = self.entry1.get()
        if entry1_text == "":
            print(">>>", end=" ")
            self.print_with_color("discover: Please enter a client_address!\n", "red")
        else:
            print(">>> ")
            self.print_with_color("discover " + entry1_text, "blue")

    def button_ping_action(self):
        entry2_text = self.entry2.get()
        if entry2_text == "":
            print(">>>", end=" ")
            self.print_with_color("ping: Please enter a client_address!\n", "red")
        else:
            print(">>> ")
            self.print_with_color("ping " + entry2_text, "blue")

    def print_with_color(self, msg, color: str):
        self.console_text.insert(tk.END, msg, color)

    def copy(self, event):
        text = self.console_text.get(tk.SEL_FIRST, tk.SEL_LAST)
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)

    def paste(self, event):
        text = self.clipboard_get()
        self.console_text.insert(tk.INSERT, text)

class ConsoleTextRedirector:
    def __init__(self, console_text_widget):
        self.console_text_widget = console_text_widget

    def write(self, msg):
        self.console_text_widget.insert(tk.END, msg)

    def flush(self):
        pass


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
            my_terminal.console_text.insert("end", f"\nClosing server socket!\n>>>")
            my_terminal.console_text.mark_set("input", "insert")
            for addr in self.client:
                self.client[addr][0].send(pickle.dumps("quit"))
                self.client[addr][0].close()
            server_socket.close()

        def ping_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.console_text.insert("end", f"\nPinging {client_addr}...\n>>>")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.send(pickle.dumps("ping"))
            start_time = time.time()
            while time.time() - start_time < 5:
                if self.command_for_client["data"]:
                    my_terminal.console_text.insert("end", f"\n{client_addr} responded!\n>>>")
                    my_terminal.console_text.mark_set("input", "insert")
                    return
            my_terminal.console_text.insert("end", f"\n{client_addr} is not responding.\n>>>")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.close()
            self.client.pop(client_addr)
            return

        def discover_command(client_addr):
            client_socket = self.client[client_addr][0]
            my_terminal.console_text.insert("end", f"\nDiscovering {client_addr}...\n>>>")
            my_terminal.console_text.mark_set("input", "insert")
            client_socket.send(pickle.dumps("discover"))
            while True:
                if self.command_for_client["data"] is not None:
                    list_of_files = self.command_for_client["data"]
                    break
            self.client[client_addr][2] = list_of_files
            my_terminal.console_text.insert("end", f"\nFiles on {client_addr}: {list_of_files}\n>>>")
            my_terminal.console_text.mark_set("input", "insert")

        def print_help():
            help_str = """
help - Print all commands and usage
list - List all client with files
ping client_addr - Live check client at client_addr
discover client_addr - Discover files in local repository of client at client_addr
quit - Shut down server socket, use this command before closing the terminal
>>> 
            """
            my_terminal.console_text.insert("end", f"{help_str}")
            my_terminal.console_text.mark_set("input", "insert")

        command = my_terminal.console_text.get("end-2l", "end-1c")
        start_index = next((i for i, char in enumerate(command) if char.isalpha()), None)
        if start_index is not None:
            command = command[start_index:]
        print(str(command))
        
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
                    my_terminal.console_text.insert("end", f"\n{print_str}\n>>>")
                    my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"\nNot a valid command!\nlist requires no arguments\n>>>",
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
                        my_terminal.console_text.insert("end", f"\nAddress not found!\n>>>")
                        my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end", f"\nNot a valid command!\nping requires 1 argument\n>>>"
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
                        my_terminal.console_text.insert("end", f"\nAddress not found!\n>>>")
                        my_terminal.console_text.mark_set("input", "insert")
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"\nNot a valid command!\ndiscover requires 1 argument\n>>>",
                    )
                    my_terminal.console_text.mark_set("input", "insert")

            case "quit":
                if len(args_list) == 1:
                    quit_command()
                    return "break"
                else:
                    my_terminal.console_text.insert(
                        "end",
                        f"\nNot a valid command!\nquit requires no arguments\n>>>",
                    )
                    my_terminal.console_text.mark_set("input", "insert")
            case _:
                my_terminal.console_text.insert("end", f"\nNot a valid command!\n>>>")
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
                    f"\nAccepted connection from {client_addr[0]}:{client_addr[1]} with these files: {list_of_files}\n>>>",
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
                my_terminal.console_text.insert("end", f"\nclient_listener stop!!\n>>>")
                my_terminal.console_text.mark_set("input", "insert")
                return

    def main(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_ip = "172.20.46.71"
        server_port = 65432
        server_socket.bind((server_ip, server_port))
        server_socket.listen(5)

        my_terminal = ConsoleApp()
        my_terminal.title("Server terminal")
        my_terminal.bind(
            "<Return>",
            lambda event, server_socket=server_socket, my_terminal=my_terminal: self.command_handler(
                server_socket, my_terminal
            ),
        )
        my_terminal.console_text.insert("end", f"\nListening on {server_ip}:{server_port}\n>>>")
        my_terminal.console_text.mark_set("input", "insert")

        threading.Thread(
            target=self.client_listener, args=[server_socket, my_terminal]
        ).start()

        my_terminal.mainloop()


if __name__ == "__main__":
    (Server()).main()
