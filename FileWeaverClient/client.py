import socket
import socketserver
import threading
import ast
import argparse
import configparser
import filehandler


class Config:
    def __init__(self):
        self.config_file = 'cfg.ini'
        self.cfg_parser = configparser.ConfigParser()
        try:
            self.cfg_parser.read(self.config_file)
            self._set_server_address()
            self._set_listening_address()
        except Exception:
            print('client: failed to read cfg.ini')
            exit(1)

    def _set_server_address(self):
        s = self.cfg_parser['Server']
        address = str(s['server_address'])
        port = int(s['server_port'])
        self.server_address = address
        self.server_port = port

    def _set_listening_address(self):
        c = self.cfg_parser['Client']
        address = str(c['listening_address'])
        port = int(c['listening_port'])
        self.listening_address = address
        self.listening_port = port


class Client:
    def __init__(self):
        self.parse_cargs()
        self.init_filehandler(Client._filename)
        self.init_config()
        self.init_command_endpoint()
        self.client_ready()

    def parse_cargs(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-f', '--filename')
        args = parser.parse_args()
        try:
            Client._filename = vars(args)['filename']
        except Exception:
            parser.print(help)

    def init_config(self):
        c = Config()
        Client._listening_address = c.listening_address
        Client._listening_port = c.listening_port
        Client._server_address = c.server_address
        Client._server_command_port = c.server_port

    def init_filehandler(self, filename):
        Client._filehandler = filehandler.FileHandler(filename)

    def init_command_endpoint(self):
        self.command_endpoint_thread = threading.Thread(target=self._create_command_socket)
        self.command_endpoint_thread.start()

    def _create_command_socket(self):
        try:
            self.command_socket = socketserver.TCPServer((Client._listening_address, Client._listening_port), ClientCommandHandler, True)
            address = self.command_socket.server_address
            print(f'client: created command endpoint: {address}')
            self.command_socket.serve_forever()
        except Exception as e:
            print(f'client: failure creating command endpoint:\n{e}')
            print('client: exiting now.')
            exit(1)

    def client_ready(self):
        try:
            data = []
            command = 'CLIENT_READY'
            data.append(str(command))
            data.append(str(Client._listening_address))
            data.append(str(Client._listening_port))
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
            s.connect((Client._server_address, Client._server_command_port))
            s.sendall(bytes(str(data), 'utf-8'))
            s.close()
        except Exception as e:
            print(f'client: exception server not responding:\n{e}')
            print('client: exiting now.')
            exit(0)


class ClientCommandHandler(socketserver.BaseRequestHandler):
    def handle(self):
        raw_data = self.request.recv(4048).strip()
        try:
            data = ast.literal_eval(str(raw_data, 'utf-8'))
            command = str(data[0])
        except Exception:
            command = str(raw_data, 'utf-8')
            pass
        print(f'client: server {self.request.getsockname()} connected {command}')
        if command == 'SEND_UNIQUE_CHARS_AND_LENGTH':
            data = []
            data.append(Client._filehandler.unique)
            data.append(str(Client._filehandler.length))
            self.request.sendall(bytes(str(data), 'utf-8'))
            print(f'client: sent uchars and length to {self.request.getsockname()}')
        elif command == 'GET_WEAVING_ENDPOINTS':
            endpoints = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
                s.connect((Client._server_address, Client._server_command_port))
                s.sendall(bytes('SEND_WEAVING_ENDPOINTS', 'utf-8'))
                data = str(s.recv(8096).strip(), 'utf-8')
                s.close()
                try:
                    endpoints = ast.literal_eval(str(data))
                except Exception as e:
                    print(f'client: dict ast.literal_eval() error\n{e}')
                print(f'client: received {len(endpoints)} endpoints from {self.request.getsockname()})')
                self.weave(endpoints)
            except Exception as e:
                print(f'client: exception handle() {command}\n{e}')
                pass

    def weave(self, endpoints):
        print('client: weaving...')
        try:
            buckets = Client._filehandler.buckets
            for b in buckets:
                endpoint = endpoints.get(b)
                for i in buckets.get(b):
                    # while threading.active_count() > 8:
                    #     None
                    # t = threading.Thread(target=self.stitch, args=(i, endpoint))
                    # t.start()
                    self.stitch(i, endpoint)
        except Exception as e:
            print(f'client: exception in weave {e}')
        print('client: all indexes have been sent, closing client.')
        exit(0)

    def stitch(self, index, endpoint):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0, None)
        s.connect((Client._server_address, endpoint))
        s.sendall(bytes(str(index), 'utf-8'))
        s.close()


if __name__ == '__main__':
    Client()
