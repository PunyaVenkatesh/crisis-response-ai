"""Structured-output helper with validation and one corrective retry.

LLMs return JSON that is *usually* valid. In an operational system "usually" is
not good enough, so every agent call goes through here:

    1. Ask the model for JSON matching a pydantic schema.
    2. Parse and validate it.
    3. If validation fails, hand the model its own output plus the exact
       validation error and ask it to correct itself — once.
    4. If it still fails, raise. A loud failure beats a plausible-looking plan
       built on a malformed assessment.
"""

from __future__ import annotations

import json
import re
from typing import Type, TypeVar

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> str:
    """Pull the JSON object out of a model response.

    Handles fenced code blocks and stray prose before or after the object.
    """
    fenced = _JSON_BLOCK.search(text)
    if fenced:
        return fenced.group(1).strip()

    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return text[start : end + 1]
    return text.strip()


def schema_hint(model: Type[BaseModel]) -> str:
    """A compact JSON-schema description the model can follow."""
    return json.dumps(model.model_json_schema(), indent=2)


def call_structured(
    llm,
    system_prompt: str,
    user_prompt: str,
    schema: Type[T],
    max_repairs: int = 1,
) -> T:
    """Call the LLM and return a validated instance of ``schema``."""
    messages = [
        SystemMessage(
            content=(
                f"{system_prompt}\n\n"
                "Respond with a single JSON object and nothing else. "
                "It must validate against this JSON schema:\n"
                f"{schema_hint(schema)}"
            )
        ),
        HumanMessage(content=user_prompt),
    ]

    raw = llm.invoke(messages).content

    for attempt in range(max_repairs + 1):
        try:
            return schema.model_validate_json(extract_json(raw))
        except (ValidationError, ValueError) as err:
            if attempt == max_repairs:
                raise ValueError(
                    f"{schema.__name__} validation failed after "
                    f"{max_repairs} repair attempt(s): {err}"
                ) from err

            raw = llm.invoke(
                messages
                + [
                    HumanMessage(
                        content=(
                            "Your previous response failed schema validation.\n\n"
                            f"Previous response:\n{raw}\n\n"
                            f"Validation error:\n{err}\n\n"
                            "Return the corrected JSON object only."
                        )
                    )
                ]
            ).content

    raise AssertionError("unreachable")
