from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]


class Team(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str = Field(..., description="Unique identifier for the team")
    password: Optional[str]= Field(None, description="Password for the team")
    secret_key: Optional[str] = Field(None, description="Hashed secret key for the team")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of team creation")


class Challenge(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    title: str = Field(..., description="Title of the challenge")
    description: str = Field(..., description="Detailed description of the challenge")
    initial_tokens: int = Field(..., description="Initial number of tokens for the challenge")
    free_benchmarks: int = Field(..., description="Number of free benchmarks available for the challenge")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of challenge creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last update")
    start_time: Optional[datetime] = Field(None, description="Timestamp of challenge start")
    end_time: Optional[datetime] = Field(None, description="Timestamp of challenge end")


class Task(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    team_id: str = Field(..., description="ID of the team associated with the task")
    team_name: Optional[str] = Field(None, description="Name of the team associated with the task")
    challenge_id: str = Field(..., description="ID of the challenge associated with the task")
    status: Literal["pending", "completed", "frozen"] = Field(..., description="Status of the task")
    available_tokens: float = Field(..., description="Number of tokens used for the task")
    available_benchmarks: int = Field(..., description="Number of free benchmarks available for the task")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of task creation")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of last update")
    benchmarks: list = Field(default_factory=list, description="List of benchmarks for the task")
    best_benchmark_score: Optional[float] = Field(None, description="Best benchmark score for the task")
    frozen_benchmark_score: Optional[float] = Field(None, description="Frizzed benchmark score for the task")
    last_benchmark_hash: Optional[str] = Field(None, description="Hash of the task submission")

    requested_correct_ids: List[int] = Field(default_factory=list, description="List of requested correct IDs")
