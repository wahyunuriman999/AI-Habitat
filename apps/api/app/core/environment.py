import uuid
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.conversation import Conversation
from app.models.message import Message
from app.core.runtime import RuntimeSession
from app.schemas.phase3 import Context, Observation, Intent


class HabitatEnvironment:
    """The Environment Orchestrator.
    
    Upholds I-11 (Intent Is Data, Not Execution): 
    The AI yields an Intent, and this Environment decides whether and how to execute it.
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.tools = {
            "calculator": self._tool_calculator
        }
        
    async def _tool_calculator(self, payload: dict[str, Any]) -> Observation:
        """Dummy tool executed strictly by the Environment."""
        expr = payload.get("expression", "")
        # Very safe dummy implementation
        try:
            # We strictly whitelist chars to prevent eval attacks
            allowed = set("0123456789+-*/() ")
            if not all(c in allowed for c in expr):
                return Observation(event="tool_error", content="Invalid characters in expression.")
            result = eval(expr)
            return Observation(event="tool_result", content=str(result))
        except Exception as e:
            return Observation(event="tool_error", content=str(e))

    async def run_loop(self, runtime: RuntimeSession, conversation_id: uuid.UUID, initial_observation: Observation) -> list[Message]:
        """Runs the Environment-Agent loop until the Runtime yields a REPLY intent."""
        
        # Load conversation history for context (just basic logic here)
        msg_res = await self.session.execute(
            select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        )
        messages = msg_res.scalars().all()
        
        # Build Context projection
        context = Context(
            habitat_id=runtime.habitat_id,
            habitat_name="Active Habitat", # Simplified
            ai_identity_name="AI",
            available_tools=list(self.tools.keys())
        )
        
        current_observation = initial_observation
        max_turns = 5
        turn_count = 0
        new_messages = []
        
        while turn_count < max_turns:
            turn_count += 1
            
            # 1. Runtime thinks and produces Intent
            intent = runtime.tick(context, current_observation)
            
            # 2. Environment Policy Boundary evaluates Intent
            if intent.intent_type == "REPLY":
                # Create the Assistant Message
                reply_msg = Message(
                    conversation_id=conversation_id,
                    role="assistant",
                    content=intent.payload.get("message", ""),
                    sender_ai_identity_id=runtime.ai_identity_id
                )
                self.session.add(reply_msg)
                new_messages.append(reply_msg)
                break
                
            elif intent.intent_type == "TOOL_CALL":
                tool_name = intent.payload.get("tool_name")
                
                # Check Environment Authorization
                if tool_name not in self.tools:
                    current_observation = Observation(event="tool_error", content="Tool not authorized or found.")
                    continue
                    
                # Environment Executes the side-effect (I-11 compliance)
                tool_func = self.tools[tool_name]
                current_observation = await tool_func(intent.payload.get("tool_args", {}))
                
                # Optionally record tool execution in memory
                tool_msg = Message(
                    conversation_id=conversation_id,
                    role="tool",
                    content=current_observation.content,
                    tool_call_id=tool_name
                )
                self.session.add(tool_msg)
                new_messages.append(tool_msg)
                
            else:
                # Reject unknown intents
                current_observation = Observation(event="error", content="Unknown intent type.")
                
        # Commit the persistent interaction log
        await self.session.commit()
        return new_messages
