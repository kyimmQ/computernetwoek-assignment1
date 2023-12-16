import socket
import os
import pickle
import threading
import shutil
import tkinter as tk
from tkinter import scrolledtext
import sys
sys.path.append('../')
from console_text_redirector import ConsoleTextRedirector

class ConsoleAppClient(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("File Transfer Client")
        self.geometry("600x400")

        label_app = tk.Label(self, text="File-sharing application", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_app.pack(side=tk.TOP, pady=10)
        label_side = tk.Label(self, text="Client side", font=("Arial", 16, "bold"), fg="blue", bg="#F0F0F0")
        label_side.pack(side=tk.TOP)

        button_frame = tk.Frame(self, bg="#D0D0D0")
        button_frame.pack(side=tk.TOP, fill=tk.X)

        button_help = tk.Button(button_frame, text="Help", command=self.button_help_action, bg="#90EE90")
        button_help.grid(row=0, column=0, padx=5, pady=5)

        button_publish = tk.Button(button_frame, text="Publish", command=self.button_publish_action, bg="#FFD700")
        button_publish.grid(row=1, column=0, padx=5, pady=5)
        self.entry_publish_lname = tk.Entry(button_frame)
        self.entry_publish_lname.grid(row=1, column=1, padx=5, pady=5)
        self.entry_publish_fname = tk.Entry(button_frame)
        self.entry_publish_fname.grid(row=1, column=2, padx=5, pady=5)

        button_fetch = tk.Button(button_frame, text="Fetch", command=self.button_fetch_action, bg="#FFD700")
        button_fetch.grid(row=2, column=0, padx=5, pady=5)
        self.entry_fetch = tk.Entry(button_frame)
        self.entry_fetch.grid(row=2, column=1, padx=5, pady=5)

        console_frame = tk.Frame(self, bg="#F0F0F0")
        console_frame.pack(fill=tk.BOTH, expand=True)

        self.console_text = scrolledtext.ScrolledText(console_frame, wrap=tk.WORD, font=("Arial", 12), bg="#F0F0F0", fg="#333333")  # Dark gray text on light gray background
        self.console_text.pack(fill=tk.BOTH, expand=True)

        self.console_text.insert(tk.END, ''' Welcome to file transferring application! 
 This is the CLIENT side!
''')

        sys.stdout = ConsoleTextRedirector(self.console_text)

        self.console_text.tag_configure("red", foreground="red")
        self.console_text.tag_configure("blue", foreground="blue")

    def button_help_action(self):
        # print(">>>", end=" ")
        self.print_with_color("Help\n", "blue")
        print('''fetch fname - Send a fetch request to server to fetch file with name at fname
publish path_to_file fname - Make a copy of the file at path_to_file to the local repository\nand send that information to server
quit - Shut down client socket.
''')
        self.console_text.mark_set('insert', 'end')

    def button_publish_action(self):
        entry_publish_lname_text = self.entry_publish_lname.get()
        entry_publish_fname_text = self.entry_publish_fname.get()
        if entry_publish_lname_text == "":
            # print(">>>", end=" ")
            self.print_with_color("publish: Please enter a lname and a fname!\n", "red")
            self.console_text.mark_set('insert', 'end')
        else:
            # print(">>> ")
            self.print_with_color("publish " + entry_publish_lname_text + " " + entry_publish_fname_text, "blue")
            self.console_text.mark_set('insert', 'end')

    def button_fetch_action(self):
        entry_fetch_text = self.entry_fetch.get()
        if entry_fetch_text == "":
            # print(">>>", end=" ")
            self.print_with_color("fetch: Please enter a fname!\n", "red")
            self.console_text.mark_set('insert', 'end')
        else:
            # print(">>> ")
            self.print_with_color("fetch " + entry_fetch_text, "blue")
            self.console_text.mark_set('insert', 'end')

    def print_with_color(self, msg, color: str):
        self.console_text.insert(tk.END, msg, color)
        self.console_text.see(tk.END)
        self.console_text.mark_set('insert', 'end')


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
                command = my_terminal.console_text.get("end-2l", "end-1c")
                
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
                        my_terminal.console_text.insert('end', f'Error while fetching: {e}\n\n')
                        my_terminal.console_text.mark_set('input', 'insert')
                    self.is_choosing = False
                    # print("Fetching completed!!")
                    my_terminal.console_text.insert('end', f'Fetching completed!!\n\n')
                    my_terminal.console_text.mark_set('input', 'insert')
                    # print(action_complete)
                else:
                    start_index = next((i for i, char in enumerate(command) if char.isalpha()), None)
                    if start_index is not None:
                        command = command[start_index:]
                    # print(str(command))
                    args_list = command.split()
                    match args_list[0]:
                        case 'fetch':
                            if len(args_list) == 2:
                                self.file_name  = args_list[1]
                                if self.file_name in self.get_files_name(): 
                                    my_terminal.console_text.insert('end', f'File already exists.\n\n')
                                    my_terminal.console_text.mark_set('input', 'insert')
                                    return 'break'
                                self.server_socket.send(pickle.dumps(f'fetch {self.file_name}'))
                            else:
                                my_terminal.console_text.insert('end', f'Not a valid command!\nfetch requires one argument\n\n')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case 'publish':
                            if len(args_list) == 3: 
                                file_path = args_list[1]
                                file_name = args_list[2]
                                dest = os.getcwd() + '\\' + self.local_dir + file_name
                                shutil.copyfile(file_path, dest)
                                self.server_socket.send(pickle.dumps(f'publish {file_name}'))
                            else:
                                my_terminal.console_text.insert('end', f'Not a valid command!\npublish requires two arguments\n\n')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case 'quit':
                            if len(args_list) == 1:
                                my_terminal.console_text.insert('end', f'Closing client socket!\n\n')
                                my_terminal.console_text.mark_set('input', 'insert')
                                if self.socket_for_upload: self.socket_for_upload.close()
                                self.server_socket.send(pickle.dumps('quit'))
                                
                                self.server_socket.close()
                                
                                return 'break'
                            else:
                                my_terminal.console_text.insert('end', f'Not a valid command!\nquit requires no arguments\n\n')
                                my_terminal.console_text.mark_set('input', 'insert')
                        case _:
                            my_terminal.console_text.insert('end', f'Not a valid command!\n\n')
                            my_terminal.console_text.mark_set('input', 'insert')
            except Exception as e: 
                my_terminal.console_text.insert('end', f'command_handler stop\n\n')
                my_terminal.console_text.mark_set('input', 'insert')
                return 'break'
                    
    def server_handler(self, my_terminal):
        # connect to the server
        host = ""
        with open('Server_IP.txt', 'r') as file:
            host = file.read().strip()
        port = 65432
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((host,port))
        self.server_socket.send(pickle.dumps(self.get_files_name()))
        self.my_addr = pickle.loads(self.server_socket.recv(1024))
        my_terminal.console_text.insert('end', f'Server successfully registered you at {self.my_addr[0]}:{self.my_addr[1]}\n\n')
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
                            my_terminal.console_text.insert('end', f'Server is down!!\n\n')
                            my_terminal.console_text.mark_set('input', 'insert')
                elif type(msg) is list: #when msg is a list, then the server is responding to a fetch command from the client
                    if len(msg) == 0: 
                        my_terminal.console_text.insert('end', f'File not found!!\n\n')
                        my_terminal.console_text.mark_set('input', 'insert')
                        continue
                    print_str = ''
                    for i in range(len(msg)):
                        print_str += f'{i + 1}: {msg[i]}\n'
                    my_terminal.console_text.insert('end', f'\n{print_str}')
                    my_terminal.console_text.mark_set('input', 'insert')
                    self.is_choosing = True
                    self.other_client = msg
            except Exception as e:
                my_terminal.console_text.insert('end', f'\nserver_handler stop!!\n\n')
                my_terminal.console_text.mark_set('input', 'insert')
                return
            
    def req_listener(self, my_terminal):
        # listen for fetching request from other clients
        self.socket_for_upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_for_upload.bind((self.my_addr[0],self.my_addr[1]+1))
        self.socket_for_upload.listen(5)
        my_terminal.console_text.insert('end', f'Listening on {self.my_addr[0]}:{self.my_addr[1]+1}\n\n')
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
                my_terminal.console_text.insert('end', f'Accepted connection from {req_addr[0]}:{req_addr[1]}\n\n')
                my_terminal.console_text.mark_set('input', 'insert')
                threading.Thread(target=req_handler, args=[req_socket]).start()
            except Exception as e:
                my_terminal.console_text.insert('end', f'req_listener stop!!\n\n')
                my_terminal.console_text.mark_set('input', 'insert')
                # print(e)
                return
            
    def main(self):
        my_terminal = ConsoleAppClient()
        my_terminal.title("Client terminal")
        my_terminal.bind("<Return>", lambda event, my_terminal = my_terminal: self.command_handler(my_terminal))
        
        threading.Thread(target=self.server_handler, args=[my_terminal]).start()
        
        while len(self.my_addr) == 0: 
            continue
        threading.Thread(target=self.req_listener, args=[my_terminal]).start()
        
        my_terminal.mainloop()

        
if __name__ == "__main__":
	(Client()).main()