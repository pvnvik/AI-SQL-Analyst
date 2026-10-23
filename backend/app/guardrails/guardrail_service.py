"""Guardrails AI validation service for LLM structured outputs."""

import json
import logging
from typing import Any, Dict, Optional, Tuple, Union
from guardrails import Guard
from pydantic import ValidationError
from app.guardrails.output_models import GeneratedSQLOutput, SQLRepairOutput

logger = logging.getLogger("querypilot.guardrails")

# Initialize Guardrails validators for output models
_sql_guard = Guard.for_pydantic(GeneratedSQLOutput)
_repair_guard = Guard.for_pydantic(SQLRepairOutput)


def validate_structured_sql_output(
    raw_output: Union[str, Dict[str, Any], GeneratedSQLOutput]
) -> Tuple[Optional[GeneratedSQLOutput], Optional[str]]:
    """Validate model output against GeneratedSQLOutput schema using Guardrails.

    Args:
        raw_output: JSON string, dictionary, or GeneratedSQLOutput object.

    Returns:
        Tuple of (validated_output, error_message).
        If validation succeeds, error_message is None.
    """
    if isinstance(raw_output, GeneratedSQLOutput):
        return raw_output, None

    try:
        if isinstance(raw_output, str):
            cleaned = raw_output.strip()
            # Handle markdown code blocks if wrapped in ```json
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            data = json.loads(cleaned.strip())
        elif isinstance(raw_output, dict):
            data = raw_output
        else:
            return None, f"Unsupported output type: {type(raw_output).__name__}"

        # Validate with Pydantic / Guard
        validated = GeneratedSQLOutput(**data)
        return validated, None

    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        msg = f"Structured output validation failed: {str(exc).splitlines()[0]}"
        logger.warning(msg)
        return None, msg
    except Exception as exc:
        msg = f"Unexpected error during structured output validation: {str(exc).splitlines()[0]}"
        logger.exception("Validation exception")
        return None, msg
