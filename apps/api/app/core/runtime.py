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
        
        # Mocking the Cognitive Engine logic
        provider = self.binding.provider if self.binding else "fallback_mock"
        
        intent = Intent(
            intent_type="ACKNOWLEDGE_OBSERVATION",
            payload={"processed_event": observation.event},
            provider_used=provider
        )
        
        return intent
