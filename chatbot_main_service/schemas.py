from pydantic import BaseModel, Field


class Memory(BaseModel):
    facts: list[str] = Field(
        description="List of extracted long-term facts about the user."
    )


class DocumentDecision(BaseModel):
    use_documents: bool = Field(
        description="Whether answering requires information from uploaded documents."
    )
