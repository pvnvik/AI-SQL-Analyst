"""Pydantic structured output models for LLM responses and Guardrails AI."""

from typing import List
from pydantic import BaseModel, Field, field_validator


class GeneratedSQLOutput(BaseModel):
    """Structured output expected from Gemini for SQL generation."""

    sql: str = Field(
        ...,
        description="The candidate read-only SQL query to execute.",
        min_length=5,
    )
    explanation: str = Field(
        ...,
        description="Brief explanation of how the query answers the user question.",
    )
    assumptions: List[str] = Field(
        default_factory=list,
        description="Assumptions made by the model (e.g. date filters, status checks).",
    )
    confidence: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Model-estimated confidence score between 0.0 and 1.0.",
    )

    @field_validator("sql")
    @classmethod
    def strip_and_clean_sql(cls, v: str) -> str:
        """Strip markdown fences and leading/trailing whitespace."""
        cleaned = v.strip()
        # Remove ```sql or ``` fences if present in raw string
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        if not cleaned:
            raise ValueError("Generated SQL cannot be empty.")
        return cleaned


class QuestionClassification(BaseModel):
    """Classification of the user's natural language question."""

    is_data_question: bool = Field(
        ...,
        description="True if the question asks for data or metrics from the database.",
    )
    reasoning: str = Field(
        ...,
        description="Reasoning for the classification decision.",
    )
    clarification_needed: bool = Field(
        default=False,
        description="True if question is ambiguous and requires user clarification.",
    )


class SQLRepairOutput(BaseModel):
    """Structured output for repaired SQL queries."""

    sql: str = Field(
        ...,
        description="The repaired read-only SQL query.",
        min_length=5,
    )
    fix_applied: str = Field(
        ...,
        description="Summary of the changes made to fix the error.",
    )
    confidence: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
    )

    @field_validator("sql")
    @classmethod
    def clean_repaired_sql(cls, v: str) -> str:
        cleaned = v.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()
        if not cleaned:
            raise ValueError("Repaired SQL cannot be empty.")
        return cleaned
