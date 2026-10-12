from datetime import datetime, timezone
from typing import Literal
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_validator, model_validator
from discord_models import SendRequest, ChannelResult
from message_models import MessageDraft, Snowflake


class ScheduleIn(SendRequest):
    request_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1, max_length=80)
    next_run: datetime
    interval_minutes: Literal[0, 15, 30, 60, 180, 360, 720, 1440, 10080] = 0
    max_runs: int = Field(default=1, ge=1, le=1000)
    consent: Literal[True]

    @field_validator('name')
    @classmethod
    def valid_name(cls, value):
        if not value.strip():
            raise ValueError('Podaj nazwę harmonogramu.')
        return value.strip()

    @field_validator('next_run')
    @classmethod
    def valid_time(cls, value):
        if value.tzinfo is None:
            raise ValueError('Wymagana strefa czasowa.')
        return value.astimezone(timezone.utc)

    @model_validator(mode='after')
    def valid_repeat(self):
        if self.interval_minutes == 0:
            self.max_runs = 1
        return self


class ScheduleOut(MessageDraft):
    id: str
    name: str
    bot_name: str
    channel_ids: list[Snowflake]
    next_run: datetime | None
    interval_minutes: int
    max_runs: int
    run_count: int
    state: Literal['active', 'running', 'paused', 'completed', 'error']
    created_at: datetime
    expires_at: datetime
    last_run: datetime | None = None
    last_error: str | None = None
    last_results: list[ChannelResult] = Field(default_factory=list)


class ScheduleAction(BaseModel):
    action: Literal['pause', 'resume']