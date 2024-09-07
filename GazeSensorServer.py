import socket
from typing import List


class GazepointClient:
    def __init__(self, host: str = '127.0.0.1', port: int = 4242):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self):
        self.socket.connect((self.host, self.port))
        self._send_initialization_commands()

    def _send_initialization_commands(self):
        commands: List[str] = [
            '<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n',
            '<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n',
            '<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'
        ]
        for cmd in commands:
            self.socket.send(cmd.encode())

    def receive_data(self, server: 'DataForwardingServer'):
        while True:
            data = self.socket.recv(4096).decode()
            print(f"Received data length: {len(data)}")
            server.forward_data(data)

    def close(self):
        self.socket.close()


class DataForwardingServer:
    def __init__(self, port: int = 6970):
        self.host = '0.0.0.0'
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket = None

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        print(f"Server listening on {self.host}:{self.port}")
        self.client_socket, address = self.server_socket.accept()
        print(f"Connection from {address} has been established.")

    def forward_data(self, data: str):
        if self.client_socket:
            try:
                self.client_socket.send(data.encode())
            except socket.error as e:
                print(f"Error sending data to client: {e}")
                self.client_socket.close()
                self.client_socket = None

    def close(self):
        if self.client_socket:
            self.client_socket.close()
        self.server_socket.close()

    def receive_data_from_gazepoint(self, gazepoint_client: GazepointClient):
        gazepoint_client.receive_data(self)


def main():
    server = DataForwardingServer(port=1212)
    server.start()

    gazepoint_client = GazepointClient(host='127.0.0.1', port=4242)
    gazepoint_client.connect()

    try:
        server.receive_data_from_gazepoint(gazepoint_client)
    finally:
        gazepoint_client.close()
        server.close()


if __name__ == "__main__":
    main()