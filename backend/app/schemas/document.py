import uuid

from pydantic import BaseModel, Field, field_validator

# Titles are short human labels and end up in service INFO logs. Strip every
# Unicode non-printable char (CR/LF, NUL, NEL, U+2028/U+2029 line separators,
# zero-width/bidi controls, ...) so a crafted title can't forge or split log
# lines — log injection, CWE-117 — then cap the cleaned length.
TITLE_MAX_LENGTH = 255


class DocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)

    @field_validator("title", mode="before")
    @classmethod
    def _strip_control_chars(cls, v: object) -> object:
        # mode="before": strip first so min/max_length apply to the CLEANED value
        # (an all-control-char title collapses to "" -> fails min_length=1).
        if isinstance(v, str):
            return "".join(ch for ch in v if ch.isprintable()).strip()
        return v


class DocumentResponse(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    module_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
