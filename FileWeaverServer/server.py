import socket
import socketserver
import threading
import ast
import time
import configparser


class Config:
    def __init__(self):
        self.config_file = 'cfg.ini'
        self.cfg_parser = configparser.ConfigParser()
        try:
            self.cfg_parser.read(self.config_file)
            self._set_listening_address()
        except Exception as e:
            print(f'client: failed to read cfg.ini')
            exit(1)

    def _set_listening_address(self):
        s = self.cfg_parser['Server']
        address = str(s['listening_address'])
        port = int(s['listening_port'])
        self.listening_address = address
        self.listening_port = port


class Server:
    def __init__(self):
        print(f'server: startup')
        self.init_config()
        self.init_command_endpoint()

    def init_config(self):
        c = Config()
        Server._listening_address = c.listening_address
        Server._listening_port = c.listening_port

    def init_command_endpoint(self):
        self.server_thread = threading.Thread(target=self._create_command_socket)
        self.server_thread.start()

    def _create_command_socket(self):
        try:
            self.command_socket = socketserver.TCPServer((Server._listening_address, Server._listening_port), ServerCommandHandler, True)
            address = self.command_socket.server_address
            print(f'server: created command endpoint: {address}')
            self.command_socket.serve_forever()
        except Exception as e:
            print(f'server: failure creating command endpoint:\n{e}')
            print(f'server: exiting now.')
            exit(1)


class ServerCommandHandler(socketserver.BaseRequestHandler):
    def handle(self):
        raw_data = self.request.recv(4048).strip()
        client = self.request.getsockname()
        try:
            data = ast.literal_eval(str(raw_data, 'utf-8'))
            command = str(data[0])
        except Exception as e:
            command = str(raw_data, 'utf-8')
            pass
        print(f'server: {client} connected: {command}')
        if command == 'CLIENT_READY':
            try:
                client_command = 'SEND_UNIQUE_CHARS_AND_LENGTH'
                Server._client_address = str(data[1])
                Server._client_command_port = int(data[2])
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
                s.connect((Server._client_address, Server._client_command_port))
                s.sendall(bytes(client_command, 'utf-8'))
                data = ast.literal_eval(str(s.recv(8096), 'utf-8'))
                s.close()
                print(f'server: sent {client_command} to {client}')
            except Exception as e:
                print(f'server: exception when trying to tell client to send uchars and length\n{e}')
            length = data[-1]
            uchars = data[0]
            '''
            initialize WeavingEndpointController
            tell client to retrieve endpoints
            '''
            WeaverEndpointController(uchars, length)
            try:
                client_command = 'GET_WEAVING_ENDPOINTS'
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
                s.connect((Server._client_address, Server._client_command_port))
                s.sendall(bytes(client_command, 'utf-8'))
                s.close()
            except Exception as e:
                print(f'server: exception {client_command}\n{e}')
                pass
        elif command == 'SEND_WEAVING_ENDPOINTS':
            '''
            send dictionary of previously created weaving endpoints
            '''
            self.request.sendall(bytes(str(WeaverEndpointController.weaving_endpoints), 'utf-8'))
            print(f'server: sent {len(WeaverEndpointController.weaving_endpoints)} endpoints to {self.request.getsockname()}')


class WeaverEndpointController:
    weaving_endpoints = {}
    char_list = []
    socket_list = []

    def __init__(self, uchars, length):
        self.uchars = uchars
        self.length = int(length)
        WeaverEndpointController.char_list = ['' for x in range(self.length)]
        self._create_weaving_endpoints()

    def _create_weaving_endpoints(self):
        for c in self.uchars:
            '''
            create TCP listening servers
            '''
            try:
                t = threading.Thread(target=self._create_weaving_servers, args=(c,))
                t.start()
            except Exception as e:
                print('server: error creating endpoints.')
        while len(WeaverEndpointController.weaving_endpoints) != len(self.uchars):
            None
        print(f'server: WeaverEndpointController created {len(WeaverEndpointController.weaving_endpoints)} endpoints')
        return

    def _create_weaving_servers(self, char):
        s = socketserver.TCPServer((Server._listening_address, 0), WeaverHandler, True)
        WeaverEndpointController.weaving_endpoints[char] = s.server_address[1]
        WeaverEndpointController.socket_list.append(s)
        s.serve_forever()

    def teardown():
        WeaverEndpointController.weaving_endpoints = {}
        WeaverEndpointController.char_list = []
        for s in WeaverEndpointController.socket_list:
            print(f'server: closing endpoint {s}')
            s.server_close()
        WeaverEndpointController.socket_list = []


'''
NOTE: the size of an integer, utf-8 encoded bytes object is 54 bytes
therefore recv(54) is used
'''


class WeaverHandler(socketserver.BaseRequestHandler):
    def handle(self):
        sockaddr = self.request.getsockname()
        sockport = sockaddr[1]
        data = int(str(self.request.recv(54), 'utf-8'))
        self.stitch(sockport, data)
        # t = threading.Thread(target=self.stitch, args=(sockport, data))
        # t.start()

    def stitch(self, sockport, data):
        for k in WeaverEndpointController.weaving_endpoints:
            if WeaverEndpointController.weaving_endpoints[k] == sockport:
                WeaverEndpointController.char_list[data] = k
                break
        is_done = True
        for c in WeaverEndpointController.char_list:
            if c == '':
                is_done = False
        if is_done:
            print(f'server: writing file.')
            filename = str(Miscelaneous.time_to_hash())
            with open(filename, 'wb') as f:
                for c in WeaverEndpointController.char_list:
                    f.write(c)
            print(f'server: file {filename} has been written')
            print(f'server: closing {len(WeaverEndpointController.socket_list)} weaving endpoints')
            WeaverEndpointController.teardown()
            exit(0)


class Miscelaneous():
    def time_to_hash():
        return hash(time.time())


if __name__ == '__main__':
    Server()
