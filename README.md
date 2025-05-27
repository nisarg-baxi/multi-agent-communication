# Multi-Agent Communication System

A robust multi-agent system for trip planning using ZeroMQ (ZMQ) and the Multi-Agent Communication Protocol (MCP).

## Features

- **Modern Architecture**: Built with ZeroMQ for efficient inter-process communication
- **Protocol-Based Communication**: Implements MCP (Multi-Agent Communication Protocol) for structured agent interactions
- **Specialized Agents**:
  - Planner Agent: Coordinates trip planning and manages requests
  - Travel Agent: Provides travel options and handles bookings
  - Hotel Agent: Manages hotel options and reservations
- **Conversation Tracking**: Maintains conversation history and context
- **Error Handling**: Robust error handling and logging
- **Asynchronous Operations**: Built with asyncio for non-blocking operations

## Prerequisites

- Python 3.8+
- ZeroMQ (pyzmq)
- Apple Silicon compatible (M1/M2/M3)

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/multi-agent-communication.git
cd multi-agent-communication
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Start the agents:

```bash
python main.py
```

2. Send a trip request:

```python
import zmq
import json
from agents.mcp_message import MCPMessage, MCPPerformatives

# Create ZMQ context and socket
context = zmq.Context()
socket = context.socket(zmq.PAIR)
socket.connect("tcp://localhost:5555")  # Connect to planner agent

# Create trip request
request = MCPMessage(
    performative=MCPPerformatives.REQUEST,
    content=json.dumps({
        "trip_id": "TRIP-001",
        "destination": "Goa",
        "dates": {
            "check_in": "2024-04-01",
            "check_out": "2024-04-07"
        }
    }),
    sender="client",
    receiver="planner"
)

# Send request
socket.send_json(request.to_json())
```

## Agent Communication Protocol (MCP)

The system uses a structured communication protocol with the following performatives:

- `REQUEST`: Initial request for action
- `INFORM`: Provide information
- `QUERY`: Ask for information
- `RESPONSE`: Response to query
- `PROPOSE`: Propose a solution
- `ACCEPT`: Accept a proposal
- `REJECT`: Reject a proposal
- `FAILURE`: Report failure
- `CFP`: Call for proposals
- `CONFIRM`: Confirm an action
- `DISCONFIRM`: Disconfirm an action

### Message Format

```json
{
  "protocol": "MCP-1.0",
  "performative": "REQUEST",
  "content": "message content",
  "sender": "agent_id",
  "receiver": "target_agent_id",
  "conversation_id": "uuid",
  "timestamp": "ISO-8601 timestamp"
}
```

## Project Structure

```
multi-agent-communication/
├── agents/
│   ├── __init__.py
│   ├── base_agent.py      # Base agent implementation
│   ├── planner_agent.py   # Trip planning coordinator
│   ├── travel_agent.py    # Travel options provider
│   ├── hotel_agent.py     # Hotel options provider
│   └── mcp_message.py     # MCP message implementation
├── config.py              # Configuration settings
├── main.py               # Application entry point
├── requirements.txt      # Project dependencies
└── README.md            # Project documentation
```

## Supported Destinations

Currently supported destinations with pre-configured options:

### Goa

- Travel Options:
  - Air India Flight (₹5000, 2h)
  - Konkan Express Train (₹2000, 12h)
  - Luxury AC Bus (₹1500, 14h)
- Hotel Options:
  - Taj Exotica (Luxury, ₹15000/night)
  - Holiday Inn (Mid-range, ₹8000/night)
  - Beach Resort (Budget, ₹4000/night)

### Mumbai

- Travel Options:
  - IndiGo Flight (₹4000, 1.5h)
  - Rajdhani Express Train (₹1800, 10h)
  - Deluxe Bus (₹1200, 12h)
- Hotel Options:
  - Taj Mahal Palace (Luxury, ₹20000/night)
  - Grand Hyatt (Luxury, ₹18000/night)
  - Comfort Inn (Mid-range, ₹6000/night)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ZeroMQ for the communication framework
- Python asyncio for asynchronous operations
- The multi-agent systems community for inspiration
