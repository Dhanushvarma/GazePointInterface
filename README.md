# GazePointInterface

A Python interface for GazePoint eye trackers with simulation support. This package provides functionality for:
- Connecting to GazePoint eye trackers
- Data forwarding server for real-time eye tracking data
- Simulation client for testing and development

## Installation

```bash
# Clone the repository
git clone https://github.com/Dhanushvarma/GazePointInterface.git

# Install in development mode
cd GazePointInterface
pip install -e .
```

## Usage

### GazePoint Server
```python
from gazepointinterface import GazepointClient, DataForwardingServer

# Initialize and start server
server = DataForwardingServer(port=1212)
server.start()

# Connect to GazePoint device
client = GazepointClient(host='127.0.0.1', port=4242)
client.connect()

# Start receiving data
try:
    client.receive_data(server)
except KeyboardInterrupt:
    client.close()
    server.close()
```

### Simulation Client
```python
from gazepointinterface import SimGazeClient, GazeDataUtil

# Initialize gaze data processor
gaze_util = GazeDataUtil(screen_width=1920, screen_height=1080)

# Connect to simulation server
client = SimGazeClient(host='localhost', port=5478)
client.connect()

# Get gaze data
message = client.get_latest_message()
```

## Requirements
- Python >= 3.6
- NumPy