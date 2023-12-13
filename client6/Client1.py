import socket
import os
import pickle
import threading
import shutil
import tkinter as tk
from tkinter import scrolledtext
import sys

class ConsoleApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Transfer Cliont")
        self.geometry("600x400")

        label_app = tk.Label(self, text="File-sharing application", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_app.pack(side=tk.TOP, pady=10)
        label_side = tk.Label(self, text="Client side", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
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
 This is the CLIENT side!
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


action_complete = '-------------------------------------------------------'

class Client:
    def __init__(self) -> None:
        self.local_dir = 'repository\\'
        self.my_addr = []
        self.is_choosing = False
        self.server_socket = None
        self.socket_for_upload = None
        self.other_client = []
        
    def get_files_name(self):
        return os.listdir(self.local_dir)
        
    def command_handler(self, my_terminal):
        
            try:
                command = my_terminal.get('input', 'end')
                
                if self.is_choosing:
                    choice = self.other_client[int(command) - 1]
                    fetch_ip, fetch_port = (choice[0], choice[1]+1)
                    # self.server_socket.send(pickle.dumps('fetching!'))
                    
                    try:
                        fetch_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        fetch_socket.connect((fetch_ip,fetch_port))
                        fetch_socket.send(pickle.dumps(self.file_name))

                        with open(f'{self.local_dir}{self.file_name}','wb') as file:
                            while True:
                                chunk = fetch_socket.recv(1024)
                                if not chunk: break
                                file.write(chunk)
                                fetch_socket.send('data received.'.encode('utf-8'))
                        fetch_socket.close()
                        # self.server_socket.send(pickle.dumps('fetch completed!'))
                        
                    except Exception as e:
                        # print(f'Error while fetching: {e}')
                        my_terminal.console_text.insert('end', f'\nError while fetching: {e}\n>>>')
                        my_terminal.console_text.mark_set('input', 'insert')
                    self.is_choosing = False
                    # print("Fetching completed!!")
                    my_terminal.console_text.insert('end', f'\nFetching completed!!\n>>>')
                    my_terminal.console_text.mark_set('input', 'insert')
                    # print(action_complete)
                else:    
                    args_list = command.split()
                    match args_list[0]:
                        case 'help':
                            if len(args_list) == 1:
                                help_str ='''help - Print all commands and usage
fetch fname - Send a fetch request to server to fetch file with name at fname
publish path_to_file fname - Make a copy of the file at path_to_file to the local repository\nand send that information to server
quit - Shut down client socket.
>>> '''                          
                                self.insert('end', f'{help_str}')
                                my_terminal.console_text.mark_set('input', 'insert')
                            else:
                                my_terminal.console_text.insert('end', f'\nNot a valid command!\nhelp requires no arguments\n>>>')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case 'fetch':
                            if len(args_list) == 2:
                                self.file_name  = args_list[1]
                                if self.file_name in self.get_files_name(): 
                                    my_terminal.console_text.insert('end', f'\nFile already exists.\n>>>')
                                    my_terminal.console_text.mark_set('input', 'insert')
                                    return 'break'
                                self.server_socket.send(pickle.dumps(f'fetch {self.file_name}'))
                            else:
                                my_terminal.console_text.insert('end', f'\nNot a valid command!\nfetch requires one argument\n>>>')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case 'publish':
                            if len(args_list) == 3: 
                                file_path = args_list[1]
                                file_name = args_list[2]
                                dest = os.getcwd() + '\\' + self.local_dir + file_name
                                shutil.copyfile(file_path, dest)
                                self.server_socket.send(pickle.dumps(f'publish {file_name}'))
                            else:
                                my_terminal.console_text.insert('end', f'\nNot a valid command!\npublish requires two arguments\n>>>')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case 'quit':
                            if len(args_list) == 1:
                                my_terminal.console_text.insert('end', f'\nClosing client socket!\n>>>')
                                my_terminal.console_text.mark_set('input', 'insert')
                                if self.socket_for_upload: self.socket_for_upload.close()
                                self.server_socket.send(pickle.dumps('quit'))
                                
                                self.server_socket.close()
                                
                                return 'break'
                            else:
                                my_terminal.console_text.insert('end', f'\nNot a valid command!\nquit requires no arguments\n>>>')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case _:
                            my_terminal.console_text.insert('end', f'\nNot a valid command!\n>>>')
                            my_terminal.console_text.mark_set('input', 'insert')
            except Exception as e: 
                my_terminal.console_text.insert('end', f'\ncommand_handler stop\n>>>')
                my_terminal.console_text.mark_set('input', 'insert')
                return 'break'
                    
    def server_handler(self, my_terminal):
        # connect to the server
        host = "172.20.46.71"
        port = 65432
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((host,port))
        self.server_socket.send(pickle.dumps(self.get_files_name()))
        self.my_addr = pickle.loads(self.server_socket.recv(1024))
        my_terminal.console_text.insert('end', f'\nServer successfully registered you at {self.my_addr[0]}:{self.my_addr[1]}\n>>>')
        my_terminal.console_text.mark_set('input', 'insert')
        # listen for server msg
        while True:
            try:
                msg = pickle.loads(self.server_socket.recv(1024))
                if type(msg) is str: # when msg is a str, then it is a command from servver
                    match msg:
                        case "ping":
                            self.server_socket.send(pickle.dumps('Alive'))
                        case 'discover':
                            self.server_socket.send(pickle.dumps(self.get_files_name()))
                        case 'quit':
                            my_terminal.console_text.insert('end', f'\nServer is down!!\n>>>')
                            my_terminal.console_text.mark_set('input', 'insert')
                elif type(msg) is list: #when msg is a list, then the server is responding to a fetch command from the client
                    if len(msg) == 0: 
                        my_terminal.console_text.insert('end', f'\nFile not found!!\n>>>')
                        my_terminal.console_text.mark_set('input', 'insert')
                        continue
                    print_str = ''
                    for i in range(len(msg)):
                        print_str += f'{i + 1}: {msg[i]}\n'
                    my_terminal.console_text.insert('end', f'\n{print_str}>>>')
                    my_terminal.console_text.mark_set('input', 'insert')
                    self.is_choosing = True
                    self.other_client = msg
            except Exception as e:
                my_terminal.console_text.insert('end', f'\nserver_handler stop!!\n>>>')
                my_terminal.console_text.mark_set('input', 'insert')
                return
            
    def req_listener(self, my_terminal):
        # listen for fetching request from other clients
        self.socket_for_upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_for_upload.bind((self.my_addr[0],self.my_addr[1]+1))
        self.socket_for_upload.listen(5)
        my_terminal.console_text.insert('end', f'\nListening on {self.my_addr[0]}:{self.my_addr[1]+1}\n>>>')
        my_terminal.console_text.mark_set('input', 'insert')
        def req_handler(req_socket):
            # handle send
            file_name = pickle.loads(req_socket.recv(1024))
            file_path = f'{self.local_dir}{file_name}'
            try:
                with open(file_path, 'rb') as file:
                    while True:
                        chuck = file.read(1024)
                        if not chuck: break
                        req_socket.send(chuck)
                        msg = req_socket.recv(1024).decode('utf-8')
                req_socket.close()
            except Exception as e:
                return
            req_socket.close()
            return
                      
        while True:
            try:
                req_socket, req_addr = self.socket_for_upload.accept()
                my_terminal.console_text.insert('end', f'\nAccepted connection from {req_addr[0]}:{req_addr[1]}\n>>>')
                my_terminal.console_text.mark_set('input', 'insert')
                threading.Thread(target=req_handler, args=[req_socket]).start()
            except Exception as e:
                my_terminal.console_text.insert('end', f'\nreq_listener stop!!\n>>>')
                my_terminal.console_text.mark_set('input', 'insert')
                # print(e)
                return
            
    def main(self):
        my_terminal = ConsoleApp()
        my_terminal.title("Client terminal")
        my_terminal.bind("<Return>", lambda event, my_terminal = my_terminal: self.command_handler(my_terminal))
        
        threading.Thread(target=self.server_handler, args=[my_terminal]).start()
        
        while len(self.my_addr) == 0: 
            continue
        threading.Thread(target=self.req_listener, args=[my_terminal]).start()
        
        my_terminal.mainloop()

        
if __name__ == "__main__":
	(Client()).main()