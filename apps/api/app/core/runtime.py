import uuid
from app.schemas.phase3 import Context, Observation, Intent
from app.models.cognitive_binding import CognitiveBinding


class RuntimeSession:
    """Ephemeral execution environment for an AIIdentity's cognitive process.
    
    Adheres to:
    - I-10 (Runtime Non-Identity): Purely volatile. No DB writes.
    - I-11 (Intent Is Data): Outputs Intent, does not execute.
    """

    def __init__(self, ai_identity_id: uuid.UUID, habitat_id: uuid.UUID, binding: CognitiveBinding | None):
        self.ai_identity_id = ai_identity_id
        self.habitat_id = habitat_id
        self.binding = binding
        # Scratchpad represents volatile state
        self.scratchpad: list[str] = []

    def tick(self, context: Context, observation: Observation) -> Intent:
        """Processes an observation and context to yield an intent."""
        
        self.scratchpad.append(f"Observed: {observation.event}")
        provider = self.binding.provider if self.binding else "fallback_mock"
        
        # MOCK COGNITIVE ENGINE LOGIC FOR PHASE 5
        # If the human asks a math question, we use the calculator tool.
        if observation.event == "user_message" and "calculate" in str(observation.content).lower():
            return Intent(
                intent_type="TOOL_CALL",
                payload={"tool_name": "calculator", "tool_args": {"expression": "2+2"}},
                provider_used=provider
            )
            
        # If the environment returns a tool result, we reply to the user.
        if observation.event == "tool_result":
            return Intent(
                intent_type="REPLY",
                payload={"message": f"The result is {observation.content}"},
                provider_used=provider
            )
        
        # Default fallback reply
        return Intent(
            intent_type="REPLY",
            payload={"message": f"Processed: {observation.content}"},
            provider_used=provider
        )
