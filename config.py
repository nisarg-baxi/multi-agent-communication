# ZMQ Communication endpoints
AGENT_ENDPOINTS = {
    "planner": "tcp://127.0.0.1:5555",
    "travel": "tcp://127.0.0.1:5556",
    "hotel": "tcp://127.0.0.1:5557"
}

# Message types
MESSAGE_TYPES = {
    "REQUEST": "request",
    "RESPONSE": "response",
    "INFORM": "inform"
}