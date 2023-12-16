import socket


class GazepointClient:
    def __init__(self, host='127.0.0.1', port=4242):
        self.host = host  # SENSOR PARAM
        self.port = port  # SENSOR PARAM
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Client socket (Windows) <- Gaze Sensor(Server)

    def connect(self):
        self.socket.connect((self.host, self.port))  # Socket Connection
        self.send_commands()  # GazePoint Sensor Init Commands

    def send_commands(self):  # Commands to send to the gazepoint sensor to make it start transmission
        commands = [
            '<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n',
            '<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n',
            '<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'
        ]
        for cmd in commands:
            self.socket.send(cmd.encode())

    def receive_data(self, server):  # Takes data from the Sensor and ports it to the server
        while True:
            data = self.socket.recv(1024).decode()  # Buffer Size for Sensor Data
            server.forward_data(data)  # This server object corresponds to the DataForwarding Server

    def close(self):
        self.socket.close()


class DataForwardingServer:
    def __init__(self, port=12345):  # Match the port on Linux Machine
        self.host = '0.0.0.0'  # Set to '0.0.0.0' to listen to all requests
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Socket Init
        self.client_socket = None  # Corresponds to the Linux Client

    def start(self):
        self.server_socket.bind((self.host, self.port))  # Binding the server
        self.server_socket.listen(1)  # Listen for incoming attempts
        print(f"Server listening on {self.host}:{self.port}")
        self.client_socket, address = self.server_socket.accept()  # Connection with client (Linux) established
        print(f"Connection from {address} has been established.")

    def forward_data(self, data):  # Function to forward data to the connected Client (Linux)
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

    def receive_data_from_gazepoint(self, gazepoint_client):  # Function to gather data from the Sensor Client
        gazepoint_client.receive_data(self)


def main():
    server = DataForwardingServer(port=12345)  # Use the port for your data forwarding server
    server.start()

    gazepoint_client = GazepointClient(host='127.0.0.1', port=4242)  # Host and port of Gazepoint Sensor Server
    gazepoint_client.connect()  # Connection established with the sensor

    try:
        server.receive_data_from_gazepoint(gazepoint_client)
    finally:
        gazepoint_client.close()
        server.close()


if __name__ == "__main__":
    main()
