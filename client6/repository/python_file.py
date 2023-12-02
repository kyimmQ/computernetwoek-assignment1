import socket
import os
import pickle
import threading
import shutil



class Client:
    def __init__(self) -> None:
        self.local_dir = 'repository\\'
        self.my_addr = None
        
    def get_files_name(self):
        return os.listdir(self.local_dir)
        
    def command_handler(self, client_socket):
        while True:
            try:
                command = input()
                args_list = command.split()
                match args_list[0]:
                    case 'fetch':
                        file_name  = args_list[1]
                        
                    case 'publish':
                        file_path = args_list[1]
                        file_name = args_list[2]
                        dest = os.getcwd() + '\\' + self.local_dir + file_name
                        shutil.copyfile(file_path, dest)
                        client_socket.send(pickle.dumps(f'publish {file_name}'))
                    case 'quit':
                        print('Closing client socket!')
                        client_socket.send(pickle.dumps('quit'))
                        client_socket.close()
                        return
                    case _:
                        print('Not a valid command!')
            except: 
                return
                    
    def server_handler(self, client_socket):
        while True:
            try:
                msg = pickle.loads(client_socket.recv(1024))
                match msg:
                    case "ping":
                        client_socket.send(pickle.dumps('Alive'))
                    case 'discover':
                        client_socket.send(pickle.dumps(self.get_files_name()))
                    case 'quit':
                        print('Server is down!')
            except:
                return
    def req_handler(self): #handle
        pass

        
        
        
    def main(self):
        host = "127.0.0.1" # localhost
        port = 65432       # The same as server uses
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host,port))
        self.server_connection = True
        client_socket.send(pickle.dumps(self.get_files_name()))
        self.my_addr = pickle.loads(client_socket.recv(1024))
        print(f'Server successfully registered at {self.my_addr[0]}:{self.my_addr[1]}')
        
        
        threading.Thread(target=self.command_handler, args=[client_socket]).start()
        
        threading.Thread(target=self.server_handler, args=[client_socket]).start()
        
        threading.Thread(target=self.req_handler)
                
        
if __name__ == "__main__":
	(Client()).main()