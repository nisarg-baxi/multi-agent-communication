# Multi-Agent Trip Planning System

A distributed multi-agent system for automated trip planning using ZeroMQ for inter-agent communication. The system consists of three specialized agents that work together to plan trips: a Planner Agent, a Travel Agent, and a Hotel Agent.

## Features

- **Distributed Architecture**: Uses ZeroMQ for efficient inter-agent communication
- **Specialized Agents**:
  - Planner Agent: Coordinates the overall trip planning process
  - Travel Agent: Provides travel options (flights, trains)
  - Hotel Agent: Offers hotel accommodations
- **Structured Communication**: JSON-based message format for clear data exchange
- **Error Handling**: Robust error handling and logging
- **Flexible Planning**: Supports multiple destinations and preferences

## Prerequisites

- Python 3.9 or higher
- ZeroMQ (pyzmq)

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd multi-agent-communication
```

2. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

Run the system:

```bash
python main.py
```

The system will:

1. Initialize all agents
2. Send a trip request to the Planner agent
3. Coordinate between agents to create a trip plan
4. Display the final trip plan

## Agent Communication

The system uses a structured message format for communication:

```json
{
  "trip_id": "TRIP001",
  "destination": "Goa",
  "dates": {
    "departure": "2024-03-20",
    "return": "2024-03-27"
  },
  "preferences": {
    "budget": "mid-range",
    "travel_type": "flexible"
  }
}
```

## Project Structure

```
multi-agent-communication/
├── agents/
│   ├── base_agent.py      # Base agent implementation
│   ├── planner_agent.py   # Trip planning coordinator
│   ├── travel_agent.py    # Travel options provider
│   ├── hotel_agent.py     # Hotel options provider
│   └── message.py         # Message handling
├── config.py              # Configuration and constants
├── main.py               # Main application entry
└── requirements.txt      # Project dependencies
```

## Supported Destinations

Currently supported destinations include:

- Goa
- Mumbai

Each destination has specific travel and hotel options.

## Contributing

Feel free to submit issues and enhancement requests!
