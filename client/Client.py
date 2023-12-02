import socket
import os
import pickle
import threading
import shutil
import tkinter
from client_terminal import *

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
                        my_terminal.insert('end', f'\nError while fetching: {e}\n>>>')
                        my_terminal.mark_set('input', 'insert')
                    self.is_choosing = False
                    # print("Fetching completed!!")
                    my_terminal.insert('end', f'\nFetching completed!!\n>>>')
                    my_terminal.mark_set('input', 'insert')
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
                                my_terminal.mark_set('input', 'insert')
                            else:
                                my_terminal.insert('end', f'\nNot a valid command!\nhelp requires no arguments\n>>>')
                                my_terminal.mark_set('input', 'insert')
                        case 'fetch':
                            if len(args_list) == 2:
                                self.file_name  = args_list[1]
                                if self.file_name in self.get_files_name(): 
                                    my_terminal.insert('end', f'\nFile already exists.\n>>>')
                                    my_terminal.mark_set('input', 'insert')
                                    return 'break'
                                self.server_socket.send(pickle.dumps(f'fetch {self.file_name}'))
                            else:
                                my_terminal.insert('end', f'\nNot a valid command!\nfetch requires one argument\n>>>')
                                my_terminal.mark_set('input', 'insert')
                        case 'publish':
                            if len(args_list) == 3: 
                                file_path = args_list[1]
                                file_name = args_list[2]
                                dest = os.getcwd() + '\\' + self.local_dir + file_name
                                shutil.copyfile(file_path, dest)
                                self.server_socket.send(pickle.dumps(f'publish {file_name}'))
                            else:
                                my_terminal.insert('end', f'\nNot a valid command!\npublish requires two arguments\n>>>')
                                my_terminal.mark_set('input', 'insert')
                        case 'quit':
                            if len(args_list) == 1:
                                my_terminal.insert('end', f'\nClosing client socket!\n>>>')
                                my_terminal.mark_set('input', 'insert')
                                if self.socket_for_upload: self.socket_for_upload.close()
                                self.server_socket.send(pickle.dumps('quit'))
                                
                                self.server_socket.close()
                                
                                return 'break'
                            else:
                                my_terminal.insert('end', f'\nNot a valid command!\nquit requires no arguments\n>>>')
                                my_terminal.mark_set('input', 'insert')
                        case _:
                            my_terminal.insert('end', f'\nNot a valid command!\n>>>')
                            my_terminal.mark_set('input', 'insert')
            except Exception as e: 
                my_terminal.insert('end', f'\ncommand_handler stop\n>>>')
                my_terminal.mark_set('input', 'insert')
                return 'break'
                    
    def server_handler(self, my_terminal):
        # connect to the server
        host = "10.128.84.222" # localhost
        port = 65432       # The same as server uses
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.connect((host,port))
        self.server_socket.send(pickle.dumps(self.get_files_name()))
        self.my_addr = pickle.loads(self.server_socket.recv(1024))
        my_terminal.insert('end', f'\nServer successfully registered you at {self.my_addr[0]}:{self.my_addr[1]}\n>>>')
        my_terminal.mark_set('input', 'insert')
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
                            my_terminal.insert('end', f'\nServer is down!!\n>>>')
                            my_terminal.mark_set('input', 'insert')
                elif type(msg) is list: #when msg is a list, then the server is responding to a fetch command from the client
                    if len(msg) == 0: 
                        my_terminal.insert('end', f'\nFile not found!!\n>>>')
                        my_terminal.mark_set('input', 'insert')
                        continue
                    print_str = ''
                    for i in range(len(msg)):
                        print_str += f'{i + 1}: {msg[i]}\n'
                    my_terminal.insert('end', f'\n{print_str}>>>')
                    my_terminal.mark_set('input', 'insert')
                    self.is_choosing = True
                    self.other_client = msg
            except Exception as e:
                my_terminal.insert('end', f'\nserver_handler stop!!\n>>>')
                my_terminal.mark_set('input', 'insert')
                return
            
    def req_listener(self, my_terminal):
        # listen for fetching request from other clients
        self.socket_for_upload = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_for_upload.bind((self.my_addr[0],self.my_addr[1]+1))
        self.socket_for_upload.listen(5)
        my_terminal.insert('end', f'\nListening on {self.my_addr[0]}:{self.my_addr[1]+1}\n>>>')
        my_terminal.mark_set('input', 'insert')
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
                my_terminal.insert('end', f'\nAccepted connection from {req_addr[0]}:{req_addr[1]}\n>>>')
                my_terminal.mark_set('input', 'insert')
                threading.Thread(target=req_handler, args=[req_socket]).start()
            except Exception as e:
                my_terminal.insert('end', f'\nreq_listener stop!!\n>>>')
                my_terminal.mark_set('input', 'insert')
                # print(e)
                return
            
    
    
    
        
            

        
        
        
    def main(self):
        
        
        
        # threading.Thread(target=self.command_handler, args=[]).start()
        root = tk.Tk()
        root.title("Client terminal")
        my_terminal = ConsoleText(root, bg='black', fg='white', insertbackground='white')
        my_terminal.bind("<Return>", lambda event, my_terminal = my_terminal: self.command_handler(my_terminal))
        my_terminal.pack()
        
        
        threading.Thread(target=self.server_handler, args=[my_terminal]).start()
        
        # wait for server response
        while len(self.my_addr) == 0: 
            continue
        # socket_for_uploading.
        # self.req_listener()
        threading.Thread(target=self.req_listener, args=[my_terminal]).start()
        
        root.mainloop()

        
if __name__ == "__main__":
	(Client()).main()