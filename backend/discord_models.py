import re
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from message_models import MessageDraft, Snowflake



class TokenRequest(BaseModel):
    token: SecretStr
    mode: Literal['bot', 'selfbot'] = 'bot'      # <-- NOWE

    @field_validator('token')
    @classmethod
    def token_format(cls, value):
        raw = value.get_secret_value().strip()
        if raw.startswith('Bot '):
            raw = raw[4:].strip()
        # token bota ORAZ token użytkownika (base64url + kropki) przechodzą ten sam wzorzec
        if not re.fullmatch(r'[A-Za-z0-9_.-]{20,200}', raw):
            raise ValueError('Nieprawidłowy format tokenu.')
        return SecretStr(raw)


class GuildRequest(TokenRequest):
    guild_id: Snowflake


class GuildProfile(BaseModel):
    id: str
    name: str


class GuildChannelProfile(BaseModel):
    id: str
    name: str
    type: int


class ChannelRequest(TokenRequest):
    channel_id: Snowflake


class SendRequest(TokenRequest, MessageDraft):
    channel_ids: list[Snowflake] = Field(min_length=1, max_length=10)
    request_id: UUID

    @field_validator('channel_ids')
    @classmethod
    def unique_channels(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('Kanały nie mogą się powtarzać.')
        return values

    @model_validator(mode='after')
    def valid_messages(self):
        if not self.valid_for(self.channel_ids):
            raise ValueError('Każdy kanał wymaga treści lub embeda.')
        if set(self.overrides) - set(self.channel_ids):
            raise ValueError('Wariant musi należeć do wybranego kanału.')
        return self


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
    
