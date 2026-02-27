#!/usr/bin/env python3
"""
User Simulator for multi-turn evaluation.

Simulates a realistic user who holds a complete task specification and
drip-feeds it to the GEOS agent across multiple conversational turns.
The simulator generates:
  - An initial high-level instruction (partial spec)
  - Answers to agent questions (ask_user / confirm_action)
  - Follow-up instructions with additional details/constraints
  - A [TASK_COMPLETE] signal when all requirements have been communicated
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI


@dataclass
class SimulatorConfig:
    """Configuration for the user simulator LLM."""

    model: str = "anthropic/claude-sonnet-4"
    temperature: float = 0.4
    max_tokens: int = 4096
    max_user_turns: int = 10  # Max follow-up turns the simulator will produce


# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------

SIMULATOR_SYSTEM_PROMPT = """\
You are simulating a geoscientist who wants to create a GEOS/GEOSX \
simulation. You are interacting with GEOS Expert, an AI assistant that \
helps create GEOS XML input files.

You have a COMPLETE task specification (provided below), but you should \
behave like a real user interacting with a GEOS expert assistant:

1. INITIAL INSTRUCTION: When asked to provide your initial instruction, \
give a high-level description of the simulation you want. Describe the \
overall goal, the type of simulation, the key physics, and the general \
geometry. Do NOT dump the entire specification at once — leave out exact \
parameter values, detailed boundary conditions, numerical method settings, \
and output configuration.

2. ANSWERING QUESTIONS: When the assistant asks you a question, answer it \
using the information from the specification. Be direct and provide the \
specific values and details requested. If the question asks about something \
not covered in the specification, say you are not sure or defer to the \
assistant's expertise.

3. FOLLOW-UP INSTRUCTIONS: After the assistant has made progress, you may \
provide additional constraints or requirements from the specification that \
have not yet been addressed. Cover 1-3 unaddressed topics per follow-up. \
Do not repeat information already communicated.

4. CONFIRMING ACTIONS: When asked to approve an action (like writing files \
or running a simulation), approve it if it seems reasonable based on the \
specification. If the assistant's plan clearly contradicts the spec, point \
out the discrepancy.

5. COMPLETION: When all major aspects of the specification have been \
communicated and the assistant has addressed them, include the exact token \
[TASK_COMPLETE] in your response.

RULES:
- Never mention that you have a "full specification" or "task spec". You \
are a real user who knows what they want from domain experience.
- Be concise but complete when answering questions.
- Do not volunteer information the assistant has not asked about, except \
in deliberate follow-up instructions.
- Stay in character as a domain scientist, not a software engineer.
- When providing numerical values, use the exact values from the specification.

=== COMPLETE TASK SPECIFICATION (for your reference only) ===
{task_specification}
=== END OF SPECIFICATION ===
"""

GENERATE_INITIAL_INSTRUCTION_PROMPT = """\
Generate your INITIAL instruction to the assistant. This should be a \
high-level description of the simulation you want to create. Include:
- The type of simulation (e.g., solid mechanics, hydraulic fracturing, \
multiphase flow)
- The physical problem being modeled
- The general geometry and domain description
- The key physics and constitutive model types (but not exact parameter values)

Do NOT include:
- Exact numerical parameter values (e.g., Young's modulus = 10 GPa)
- Detailed boundary condition specifications
- Specific mesh parameters (cell counts, element sizes)
- Output/event configuration details
- Solver tuning parameters

Keep it to 2-4 paragraphs. Write naturally as a user talking to an assistant."""

ANSWER_QUESTION_PROMPT = """\
The assistant is asking you the following question:

---
{question}
---
{choices_text}

Answer this question using the information from the specification. \
Be direct and specific. Provide numerical values when they are in the \
specification. If the specification does not cover this topic, say so \
and defer to the assistant's judgment."""

GENERATE_FOLLOWUP_PROMPT = """\
The assistant has been working on your simulation. Here is a summary of \
the conversation so far:

---
{conversation_summary}
---

Review the full specification and identify important requirements that \
have NOT yet been communicated to the assistant. Consider:
- Boundary conditions and loads not yet specified
- Constitutive model parameters not yet provided
- Mesh details not yet discussed
- Output, events, and time-stepping configuration
- Any other specification details the assistant hasn't addressed

If there are unaddressed requirements, provide a follow-up instruction \
covering 1-3 of them. Write naturally as a user providing more details.

If everything important has been covered, respond with exactly: \
[TASK_COMPLETE]"""


class UserSimulator:
    """LLM-powered user simulator for multi-turn evaluation.

    Holds a complete task specification and simulates a realistic user
    who reveals requirements incrementally across multiple turns.
    """

    def __init__(
        self,
        task_specification: str,
        config: Optional[SimulatorConfig] = None,
        api_key: Optional[str] = None,
    ):
        self.task_specification = task_specification
        self.config = config or SimulatorConfig()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key or os.environ.get("OPENROUTER_API_KEY"),
        )
        self.system_prompt = SIMULATOR_SYSTEM_PROMPT.format(
            task_specification=task_specification,
        )
        # Conversation history from the simulator's perspective.
        # "user" = prompts from the runner, "assistant" = simulator replies.
        self.conversation_history: List[Dict[str, str]] = []
        self.turn_count: int = 0
        self.task_complete: bool = False

    def _call_llm(self, user_prompt: str) -> str:
        """Make a single LLM call with the simulator's system prompt."""
        messages = [
            {"role": "system", "content": self.system_prompt},
            *self.conversation_history,
            {"role": "user", "content": user_prompt},
        ]
        response = self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        reply = response.choices[0].message.content.strip()

        # Track conversation for context continuity
        self.conversation_history.append({"role": "user", "content": user_prompt})
        self.conversation_history.append({"role": "assistant", "content": reply})

        return reply

    def generate_initial_instruction(self) -> str:
        """Generate the first user message — a high-level, partial instruction."""
        self.turn_count += 1
        return self._call_llm(GENERATE_INITIAL_INSTRUCTION_PROMPT)

    def answer_question(
        self,
        question: str,
        choices: Optional[List[str]] = None,
        is_confirmation: bool = False,
    ) -> str:
        """Answer a question from the agent (ask_user or confirm_action).

        Args:
            question: The question text from the agent.
            choices: Optional list of choices (from ask_user).
            is_confirmation: True if this is a confirm_action request.

        Returns:
            The simulator's answer string.
        """
        self.turn_count += 1

        if is_confirmation:
            prompt = (
                f"The assistant wants to confirm the following action:\n\n"
                f"---\n{question}\n---\n\n"
                f"Based on the specification, should you approve or deny this? "
                f"Reply with 'yes' to approve or 'no' to deny, followed by "
                f"a brief explanation if you deny."
            )
        else:
            choices_text = ""
            if choices:
                choices_text = f"\nAvailable choices: {', '.join(choices)}"
            prompt = ANSWER_QUESTION_PROMPT.format(
                question=question,
                choices_text=choices_text,
            )

        return self._call_llm(prompt)

    def generate_followup(self, conversation_summary: str) -> Optional[str]:
        """Generate a follow-up instruction with more spec details.

        Args:
            conversation_summary: Summary of the conversation so far.

        Returns:
            A follow-up instruction string, or None if the task is complete.
        """
        if self.task_complete or self.turn_count >= self.config.max_user_turns:
            return None

        self.turn_count += 1
        reply = self._call_llm(
            GENERATE_FOLLOWUP_PROMPT.format(
                conversation_summary=conversation_summary,
            )
        )

        if "[TASK_COMPLETE]" in reply:
            self.task_complete = True
            return None

        return reply

    def is_done(self) -> bool:
        """Check if the simulator considers the task complete."""
        return self.task_complete or self.turn_count >= self.config.max_user_turns
