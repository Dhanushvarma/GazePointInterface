"""
A client implementation for receiving and processing gaze data from an eye tracking server
in a simulation environment. Handles XML-formatted gaze data through TCP socket communication.
"""

import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, Tuple
import logging
from contextlib import contextmanager


@dataclass
class GazeServerConfig:
    """Configuration for gaze server connection."""
    host: str
    port: int
    message_length: int
    buffer_size: int = 1024
    xml_start_tag: str = '<REC'


class SimGazeClient:
    """
    Client for receiving gaze data from an eye tracking server in a simulation environment.
    Handles connection management, data reception, and message processing in a thread-safe manner.
    """

    def __init__(self, config: GazeServerConfig):
        """
        Initialize the simulator gaze client.

        Args:
            config: GazeServerConfig object containing connection parameters
        """
        self._config = config
        self._socket: Optional[socket.socket] = None
        self._buffer: str = ''
        self._latest_message: Optional[str] = None
        self._lock = threading.Lock()
        self._running = False
        self._receive_thread: Optional[threading.Thread] = None
        
        # Set up logging
        self._logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging for the client."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self._logger.addHandler(handler)
        self._logger.setLevel(logging.INFO)

    @contextmanager
    def _socket_connection(self) -> socket.socket:
        """
        Context manager for socket operations.
        
        Yields:
            Connected socket object
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self._config.host, self._config.port))
            yield sock
        except socket.error as e:
            raise ConnectionError(f"Failed to connect to server: {e}")
        finally:
            sock.close()

    def connect(self) -> None:
        """
        Establish connection to the gaze server and start the receiving thread.
        
        Raises:
            ConnectionError: If connection cannot be established
        """
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self._config.host, self._config.port))
            self._running = True
            
            self._receive_thread = threading.Thread(
                target=self._receive_messages,
                daemon=True,
                name="GazeReceiver"
            )
            self._receive_thread.start()
            
            self._logger.info(
                f"Connected to gaze server at {self._config.host}:{self._config.port}"
            )
            
        except socket.error as e:
            self._logger.error(f"Failed to connect: {e}")
            raise ConnectionError(f"Could not connect to server: {e}")

    def _process_message(self, message: str) -> None:
        """
        Process received message and update latest message in thread-safe manner.
        
        Args:
            message: Raw message string to process
        """
        with self._lock:
            self._latest_message = message
            self._logger.debug(f"Processed message of length {len(message)}")

    def _receive_messages(self) -> None:
        """
        Continuously receive and process messages from the server.
        Runs in a separate thread.
        """
        if not self._socket:
            self._logger.error("Socket not initialized")
            return

        try:
            while self._running:
                data = self._socket.recv(self._config.buffer_size).decode()
                if not data:
                    if self._running:
                        self._logger.warning("Server closed connection")
                        break
                    return

                self._buffer += data
                self._parse_buffer()

        except socket.error as e:
            if self._running:
                self._logger.error(f"Connection error: {e}")
        finally:
            self._cleanup()

    def _parse_buffer(self) -> None:
        """Parse the buffer for complete messages using XML tags."""
        while True:
            start = self._buffer.find(self._config.xml_start_tag)
            if start == -1 or len(self._buffer) < start + self._config.message_length:
                break

            message = self._buffer[start:start + self._config.message_length]
            self._buffer = self._buffer[start + self._config.message_length:]
            self._process_message(message)

    def get_latest_message(self) -> Optional[str]:
        """
        Get the latest received message in a thread-safe manner.
        
        Returns:
            Latest message or None if no message received
        """
        with self._lock:
            return self._latest_message

    def _cleanup(self) -> None:
        """Clean up resources and reset client state."""
        if self._socket:
            self._socket.close()
            self._socket = None
        self._buffer = ''
        self._latest_message = None
        self._running = False

    def disconnect(self) -> None:
        """
        Safely disconnect from the server and clean up resources.
        """
        self._running = False
        if self._socket:
            self._socket.close()
            self._socket = None
            self._logger.info("Disconnected from the server")

    def __enter__(self) -> 'SimGazeClient':
        """Enable context manager support."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Ensure proper cleanup when used as context manager."""
        self.disconnect()


def main() -> None:
    """Example usage of the SimGazeClient."""
    config = GazeServerConfig(
        host='192.168.1.93',
        port=5478,
        message_length=102
    )

    # Using context manager for automatic connection handling
    with SimGazeClient(config) as client:
        for _ in range(5):
            time.sleep(3)
            message = client.get_latest_message()
            if message:
                print(f"Message type: {type(message)}")
                print(f"Message length: {len(message)}")
                print(f"Message content: {message}")


if __name__ == "__main__":
    main()