from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints, field_validator, model_validator

Snowflake = Annotated[str, StringConstraints(pattern=r'^[0-9]{17,20}$')]


def text_length(value, limit):
    if len(value.encode('utf-16-le')) // 2 > limit:
        raise ValueError('Przekroczono limit znaków.')
    return value


class EmbedPayload(BaseModel):
    title: str = Field(default='', max_length=256)
    description: str = Field(default='', max_length=4096)
    color: int = Field(default=7636982, ge=0, le=16777215)
    url: str = Field(default='', max_length=1000)
    footer: str = Field(default='', max_length=2048)

    @field_validator('url')
    @classmethod
    def safe_url(cls, value):
        from urllib.parse import urlparse
        parsed = urlparse(value)
        if value and (parsed.scheme not in {'http', 'https'} or not parsed.hostname or parsed.username):
            raise ValueError('Link musi mieć protokół http lub https.')
        return value

    @model_validator(mode='after')
    def lengths(self):
        for field, limit in [('title', 256), ('description', 4096), ('footer', 2048)]:
            text_length(getattr(self, field), limit)
        if len((self.title + self.description + self.footer).encode('utf-16-le')) // 2 > 6000:
            raise ValueError('Embed ma maksymalnie 6000 znaków.')
        if not (self.title.strip() or self.description.strip()):
            raise ValueError('Embed wymaga tytułu lub opisu.')
        return self

    def discord_json(self):
        result = self.model_dump(exclude={'footer'})
        result = {k: v for k, v in result.items() if v != ''}
        if self.footer:
            result['footer'] = {'text': self.footer}
        return result


class MessageDraft(BaseModel):
    content: str = Field(default='', max_length=2000)
    embed: EmbedPayload | None = None
    overrides: dict[Snowflake, str] = Field(default_factory=dict, max_length=10)

    @field_validator('content')
    @classmethod
    def check_content(cls, value):
        return text_length(value, 2000)

    @field_validator('overrides')
    @classmethod
    def check_overrides(cls, values):
        for value in values.values():
            text_length(value, 2000)
        return values

    def valid_for(self, ids):
        return all(self.overrides.get(i, self.content).strip() or self.embed for i in ids)