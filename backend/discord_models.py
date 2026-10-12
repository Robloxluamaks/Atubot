import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr, StringConstraints, field_validator

Snowflake = Annotated[str, StringConstraints(pattern=r'^[0-9]{17,20}$')]


class TokenRequest(BaseModel):
    token: SecretStr

    @field_validator('token')
    @classmethod
    def token_format(cls, value):
        raw = value.get_secret_value().strip()
        if raw.startswith('Bot '):
            raw = raw[4:].strip()
        if not re.fullmatch(r'[A-Za-z0-9_.-]{20,200}', raw):
            raise ValueError('Nieprawidłowy format tokenu bota.')
        return SecretStr(raw)


class ChannelRequest(TokenRequest):
    channel_id: Snowflake


class SendRequest(TokenRequest):
    channel_ids: list[Snowflake] = Field(min_length=1, max_length=10)
    content: str = Field(min_length=1, max_length=2000)
    request_id: UUID

    @field_validator('channel_ids')
    @classmethod
    def unique_channels(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('Kanały nie mogą się powtarzać.')
        return values

    @field_validator('content')
    @classmethod
    def valid_content(cls, value):
        if not value.strip() or len(value.encode('utf-16-le')) // 2 > 2000:
            raise ValueError('Wiadomość musi zawierać 1–2000 znaków.')
        return value


class BotProfile(BaseModel):
    id: str
    username: str
    avatar_url: str | None = None


class ChannelProfile(BaseModel):
    id: str
    name: str
    guild_id: str


class ChannelResult(BaseModel):
    channel_id: str
    channel_name: str | None = None
    status: Literal['sent', 'failed', 'unknown', 'skipped']
    detail: str
    message_id: str | None = None
    message_url: str | None = None
    retry_after: float | None = None


class SendResponse(BaseModel):
    request_id: str
    sent_at: str
    results: list[ChannelResult]