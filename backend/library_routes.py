from uuid import uuid4
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator, model_validator
from database import db, utcnow
from message_models import MessageDraft, Snowflake
from workspace_auth import owner

router = APIRouter(prefix='/api/library')


class TemplateIn(MessageDraft):
    name: str = Field(min_length=1, max_length=80)

    @model_validator(mode='after')
    def has_message(self):
        if not self.content.strip() and not self.embed and not any(v.strip() for v in self.overrides.values()):
            raise ValueError('Szablon wymaga treści lub embeda.')
        return self

    @field_validator('name')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('Podaj nazwę.')
        return value.strip()


class TemplateOut(TemplateIn):
    id: str
    created_at: datetime


class SavedChannel(BaseModel):
    id: Snowflake
    name: str = Field(min_length=1, max_length=100)


class GroupIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    channels: list[SavedChannel] = Field(min_length=1, max_length=10)

    @field_validator('name')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('Podaj nazwę.')
        return value.strip()

    @field_validator('channels')
    @classmethod
    def unique(cls, values):
        if len({v.id for v in values}) != len(values):
            raise ValueError('Duplikaty kanałów.')
        return values


class GroupOut(GroupIn):
    id: str
    created_at: datetime


async def save(collection, payload, session, item_id=None):
    if item_id:
        result = await db[collection].update_one({'id': item_id, 'owner_id': session['id']},
                                               {'$set': payload.model_dump()})
        if not result.matched_count:
            raise HTTPException(404, 'Nie znaleziono wpisu.')
    else:
        if await db[collection].count_documents({'owner_id': session['id']}) >= 100:
            raise HTTPException(400, 'Osiągnięto limit 100 wpisów.')
        item_id = str(uuid4())
        await db[collection].insert_one({**payload.model_dump(), 'id': item_id,
            'owner_id': session['id'], 'created_at': utcnow(), 'expires_at': session['expires_at']})
    return await db[collection].find_one({'id': item_id, 'owner_id': session['id']}, {'_id': 0, 'owner_id': 0, 'expires_at': 0})


@router.get('/templates', response_model=list[TemplateOut])
async def templates(session=Depends(owner)):
    return await db.templates.find({'owner_id': session['id']}, {'_id': 0}).sort('created_at', -1).to_list(100)


@router.post('/templates', response_model=TemplateOut)
async def add_template(payload: TemplateIn, session=Depends(owner)):
    return await save('templates', payload, session)


@router.put('/templates/{item_id}', response_model=TemplateOut)
async def edit_template(item_id: str, payload: TemplateIn, session=Depends(owner)):
    return await save('templates', payload, session, item_id)


@router.get('/groups', response_model=list[GroupOut])
async def groups(session=Depends(owner)):
    return await db.groups.find({'owner_id': session['id']}, {'_id': 0}).sort('created_at', -1).to_list(100)


@router.post('/groups', response_model=GroupOut)
async def add_group(payload: GroupIn, session=Depends(owner)):
    return await save('groups', payload, session)


@router.put('/groups/{item_id}', response_model=GroupOut)
async def edit_group(item_id: str, payload: GroupIn, session=Depends(owner)):
    return await save('groups', payload, session, item_id)


@router.delete('/{kind}/{item_id}')
async def remove(kind: str, item_id: str, session=Depends(owner)):
    if kind not in {'templates', 'groups'}:
        raise HTTPException(404, 'Nie znaleziono wpisu.')
    result = await db[kind].delete_one({'id': item_id, 'owner_id': session['id']})
    if not result.deleted_count:
        raise HTTPException(404, 'Nie znaleziono wpisu.')
    return {'deleted': True}