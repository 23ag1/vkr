import uuid

from pydantic import BaseModel


class GenerateRequest(BaseModel):
    module_id: uuid.UUID


class AnswerRequest(BaseModel):
    question_id: uuid.UUID
    selected_index: int


class QuestionResponse(BaseModel):
    id: uuid.UUID
    module_id: uuid.UUID
    text: str
    options: list[str]

    model_config = {"from_attributes": True}


class AnswerFeedback(BaseModel):
    is_correct: bool
    explanation: str
    correct_index: int


class AnswerHistoryItem(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    selected_index: int
    is_correct: bool

    model_config = {"from_attributes": True}
