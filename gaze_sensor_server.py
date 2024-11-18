"""
A client-server implementation for handling Gazepoint eye tracker data.
Receives data from a Gazepoint device and forwards it to connected clients.
"""

import socket
import threading
import logging
import time
from typing import List, Optional, Set
from dataclasses import dataclass
from contextlib import contextmanager

@dataclass
class GazepointConfig:
    """Configuration for Gazepoint connection."""
    host: str = '127.0.0.1'
    port: int = 4242
    buffer_size: int = 4096
    reconnect_delay: float = 5.0
    initialization_commands: List[str] = None

    def __post_init__(self):
        if self.initialization_commands is None:
            self.initialization_commands = [
                '<SET ID="ENABLE_SEND_CURSOR" STATE="1" />\r\n',
                '<SET ID="ENABLE_SEND_POG_FIX" STATE="1" />\r\n',
                '<SET ID="ENABLE_SEND_DATA" STATE="1" />\r\n'
            ]


@dataclass
class ServerConfig:
    """Configuration for data forwarding server."""
    host: str = '0.0.0.0'
    port: int = 6970
    max_clients: int = 5
    buffer_size: int = 4096


class GazepointClient:
    """Client for connecting to and receiving data from a Gazepoint eye tracker."""

    def __init__(self, config: GazepointConfig):
        """
        Initialize the Gazepoint client.

        Args:
            config: Configuration object for the Gazepoint connection
        """
        self.config = config
        self._socket: Optional[socket.socket] = None
        self._running = False
        self._connected = False
        self._logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    @contextmanager
    def _socket_connection(self) -> socket.socket:
        """Context manager for socket operations."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.config.host, self.config.port))
            yield sock
        finally:
            sock.close()

    def connect(self) -> bool:
        """
        Establish connection to the Gazepoint device.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.config.host, self.config.port))
            self._send_initialization_commands()
            self._connected = True
            self._running = True
            self._logger.info(f"Connected to Gazepoint at {self.config.host}:{self.config.port}")
            return True
        except socket.error as e:
            self._logger.error(f"Failed to connect to Gazepoint: {e}")
            return False

    def _send_initialization_commands(self) -> None:
        """Send initialization commands to the Gazepoint device."""
        if not self._socket:
            return

        for cmd in self.config.initialization_commands:
            try:
                self._socket.send(cmd.encode())
                self._logger.debug(f"Sent command: {cmd.strip()}")
            except socket.error as e:
                self._logger.error(f"Failed to send command: {e}")
                raise

    def receive_data(self, server: 'DataForwardingServer') -> None:
        """
        Continuously receive data from Gazepoint and forward to server.

        Args:
            server: Server instance to forward data to
        """
        while self._running and self._socket:
            try:
                data = self._socket.recv(self.config.buffer_size).decode()
                if not data:
                    self._logger.warning("No data received, connection may be closed")
                    break
                self._logger.debug(f"Received {len(data)} bytes")
                server.forward_data(data)
            except socket.error as e:
                self._logger.error(f"Error receiving data: {e}")
                break

    def close(self) -> None:
        """Clean up resources and close connection."""
        self._running = False
        if self._socket:
            try:
                self._socket.close()
                self._logger.info("Closed Gazepoint connection")
            except socket.error as e:
                self._logger.error(f"Error closing socket: {e}")
            finally:
                self._socket = None
                self._connected = False


class DataForwardingServer:
    """Server that forwards Gazepoint data to connected clients."""

    def __init__(self, config: ServerConfig):
        """
        Initialize the forwarding server.

        Args:
            config: Server configuration object
        """
        self.config = config
        self._server_socket: Optional[socket.socket] = None
        self._clients: Set[socket.socket] = set()
        self._running = False
        self._lock = threading.Lock()
        self._logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    def start(self) -> None:
        """Start the forwarding server and accept client connections."""
        try:
            self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self._server_socket.bind((self.config.host, self.config.port))
            self._server_socket.listen(self.config.max_clients)
            self._running = True

            self._logger.info(f"Server listening on {self.config.host}:{self.config.port}")

            # Start accepting clients in a separate thread
            threading.Thread(target=self._accept_clients, daemon=True).start()

        except socket.error as e:
            self._logger.error(f"Failed to start server: {e}")
            raise

    def _accept_clients(self) -> None:
        """Accept new client connections."""
        while self._running and self._server_socket:
            try:
                client_socket, address = self._server_socket.accept()
                with self._lock:
                    self._clients.add(client_socket)
                self._logger.info(f"New client connected from {address}")
            except socket.error as e:
                if self._running:
                    self._logger.error(f"Error accepting client: {e}")

    def forward_data(self, data: str) -> None:
        """
        Forward data to all connected clients.

        Args:
            data: Data string to forward
        """
        if not data:
            return

        with self._lock:
            disconnected_clients = set()
            for client in self._clients:
                try:
                    client.send(data.encode())
                except socket.error as e:
                    self._logger.error(f"Error forwarding data to client: {e}")
                    disconnected_clients.add(client)

            # Remove disconnected clients
            for client in disconnected_clients:
                self._clients.remove(client)
                client.close()

    def close(self) -> None:
        """Clean up resources and close all connections."""
        self._running = False
        
        # Close all client connections
        with self._lock:
            for client in self._clients:
                try:
                    client.close()
                except socket.error as e:
                    self._logger.error(f"Error closing client connection: {e}")
            self._clients.clear()

        # Close server socket
        if self._server_socket:
            try:
                self._server_socket.close()
                self._logger.info("Server shut down")
            except socket.error as e:
                self._logger.error(f"Error closing server socket: {e}")
            finally:
                self._server_socket = None


def main():
    """Main entry point for running the Gazepoint server."""
    # Configure logging for the main function
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Create server and client configurations
    server_config = ServerConfig(port=1212)
    gazepoint_config = GazepointConfig(host='127.0.0.1', port=4242)

    # Initialize server and client
    server = DataForwardingServer(server_config)
    gazepoint_client = GazepointClient(gazepoint_config)

    try:
        # Start server
        server.start()
        logger.info("Server started successfully")

        # Connect to Gazepoint
        if not gazepoint_client.connect():
            logger.error("Failed to connect to Gazepoint device")
            return

        # Start receiving and forwarding data
        gazepoint_client.receive_data(server)

    except KeyboardInterrupt:
        logger.info("Shutting down server (Ctrl+C pressed)")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        gazepoint_client.close()
        server.close()


if __name__ == "__main__":
    main()