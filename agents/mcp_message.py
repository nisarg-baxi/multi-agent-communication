import json
from datetime import datetime
import uuid

class MCPMessage:
    """
    Multi-Agent Communication Protocol (MCP) Message Format
    Based on principles of structured agent communication
    """
    def __init__(self, 
                 performative,  # Type of message (REQUEST, INFORM, QUERY, etc.)
                 content,      # Actual message content
                 sender,       # Sender agent ID
                 receiver,     # Receiver agent ID
                 conversation_id=None,  # For tracking conversation threads
                 timestamp=None,        # Message timestamp
                 protocol="MCP-1.0"):   # Protocol version
        self.performative = performative
        self.content = content
        self.sender = sender
        self.receiver = receiver
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.protocol = protocol

    def to_json(self):
        """Convert message to JSON format"""
        return json.dumps({
            "protocol": self.protocol,
            "performative": self.performative,
            "content": self.content,
            "sender": self.sender,
            "receiver": self.receiver,
            "conversation_id": self.conversation_id,
            "timestamp": self.timestamp
        })

    @classmethod
    def from_json(cls, json_str):
        """Create message from JSON string"""
        data = json.loads(json_str)
        return cls(
            performative=data["performative"],
            content=data["content"],
            sender=data["sender"],
            receiver=data["receiver"],
            conversation_id=data.get("conversation_id"),
            timestamp=data.get("timestamp"),
            protocol=data.get("protocol", "MCP-1.0")
        )

    def create_reply(self, performative, content):
        """Create a reply message in the same conversation"""
        return MCPMessage(
            performative=performative,
            content=content,
            sender=self.receiver,
            receiver=self.sender,
            conversation_id=self.conversation_id
        )

# MCP Performatives
class MCPPerformatives:
    REQUEST = "REQUEST"           # Request for action
    INFORM = "INFORM"            # Provide information
    QUERY = "QUERY"              # Ask for information
    RESPONSE = "RESPONSE"        # Response to query
    PROPOSE = "PROPOSE"          # Propose a solution
    ACCEPT = "ACCEPT"            # Accept a proposal
    REJECT = "REJECT"            # Reject a proposal
    FAILURE = "FAILURE"          # Report failure
    CFP = "CALL_FOR_PROPOSALS"   # Call for proposals
    CONFIRM = "CONFIRM"          # Confirm an action
    DISCONFIRM = "DISCONFIRM"    # Disconfirm an action 