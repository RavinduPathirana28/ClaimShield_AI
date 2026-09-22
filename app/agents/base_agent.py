import json
import uuid
import time

class BaseAgent:
    """
    Abstract base class for all agents in the ClaimShield multi-agent system.

    Implements the A2A/1.0 (Agent-to-Agent) JSON messaging protocol:
    ┌──────────────────────────────────────────────────────────┐
    │  A2A/1.0 Message Schema                                 │
    │  ─────────────────────                                   │
    │  {                                                       │
    │    "protocol": "A2A/1.0",                                │
    │    "message_id": "<UUID4>",                              │
    │    "timestamp": <unix_epoch_float>,                      │
    │    "sender": "<agent_name>",                             │
    │    "recipient": "<agent_name>",                          │
    │    "action": "<action_verb>",                            │
    │    "data": { ... }                                       │
    │  }                                                       │
    │                                                          │
    │  Transport: In-process Python function call               │
    │  Serialization: JSON (validated via dumps/loads cycle)    │
    │  Response: Same schema with added "status" field          │
    └──────────────────────────────────────────────────────────┘
    """
    PROTOCOL_VERSION = "A2A/1.0"

    def __init__(self, name: str):
        self.name = name

    def send_message(self, recipient, action: str, data: dict) -> dict:
        """
        Formats a structured A2A/1.0 JSON message, simulates transmission by
        serializing/deserializing, calls the recipient's handler, and returns
        a JSON response.
        """
        message = {
            "protocol": self.PROTOCOL_VERSION,
            "message_id": str(uuid.uuid4()),
            "timestamp": time.time(),
            "sender": self.name,
            "recipient": recipient.name,
            "action": action,
            "data": data
        }
        
        # Serialize/deserialize to strictly validate JSON compliance and isolate state
        try:
            serialized = json.dumps(message)
            msg_payload = json.loads(serialized)
        except Exception as e:
            return {
                "protocol": self.PROTOCOL_VERSION,
                "sender": self.name,
                "status": "error",
                "message": f"Serialization failure on outgoing message: {e}"
            }
            
        # Deliver the message via recipient function invocation
        resp_payload = recipient.handle_message(msg_payload)
        
        # Serialize/deserialize response payload to maintain compliance
        try:
            serialized_resp = json.dumps(resp_payload)
            return json.loads(serialized_resp)
        except Exception as e:
            return {
                "protocol": self.PROTOCOL_VERSION,
                "sender": recipient.name,
                "status": "error",
                "message": f"Serialization failure on incoming response: {e}"
            }

    def handle_message(self, message: dict) -> dict:
        """
        Processes incoming A2A messages. Subclasses must override this to implement
        agent logic.
        """
        raise NotImplementedError("Subclasses must implement handle_message method")
