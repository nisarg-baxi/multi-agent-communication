import json

class Message:
    def __init__(self, msg_type, content, sender=None, receiver=None):
        self.msg_type = msg_type
        self.content = content
        self.sender = sender
        self.receiver = receiver

    def to_json(self):
        return json.dumps({
            "type": self.msg_type,
            "content": self.content,
            "sender": self.sender,
            "receiver": self.receiver
        })

    @classmethod
    def from_json(cls, json_str):
        data = json.loads(json_str)
        return cls(
            msg_type=data["type"],
            content=data["content"],
            sender=data.get("sender"),
            receiver=data.get("receiver")
        ) 