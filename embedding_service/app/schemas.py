"""Pydantic request and response contracts for the embedding API."""

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class EmbedRequest(BaseModel):
    text: str = Field(..., min_length=1)

    @field_validator("text")
    @classmethod
    def text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty or whitespace")
        return value


class BatchEmbedRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1)

    @field_validator("texts")
    @classmethod
    def texts_not_blank(cls, values: list[str]) -> list[str]:
        if any(not isinstance(value, str) or not value.strip() for value in values):
            raise ValueError("each text must not be empty or whitespace")
        return values


class SimilarityRequest(BaseModel):
    text_a: str | None = None
    text_b: str | None = None
    vector_a: list[float] | None = None
    vector_b: list[float] | None = None

    @model_validator(mode="after")
    def validate_pair(self):
        text_pair = self.text_a is not None or self.text_b is not None
        vector_pair = self.vector_a is not None or self.vector_b is not None
        if text_pair == vector_pair:
            raise ValueError("provide either text_a/text_b or vector_a/vector_b, but not both")
        if text_pair and (not self.text_a or not self.text_a.strip() or not self.text_b or not self.text_b.strip()):
            raise ValueError("both texts must be non-empty")
        if vector_pair and (not self.vector_a or not self.vector_b):
            raise ValueError("both vectors must be non-empty")
        if vector_pair and len(self.vector_a) != len(self.vector_b):
            raise ValueError("vectors must have equal dimensions")
        return self


class EmbeddingResponse(BaseModel):
    model: str
    dim: int
    vectors: Any

