import hashlib
import hmac
import os
import secrets
from datetime import timedelta
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from database import db, utcnow

COOKIE = '__Host-relay_workspace'
router = APIRouter(prefix='/api/workspace')


def same_origin(request: Request):
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        if request.headers.get('origin') != os.environ['APP_ORIGIN']:
            raise HTTPException(403, 'Niedozwolone źródło żądania.')


def digest(raw):
    return hmac.new(bytes.fromhex(os.environ['SESSION_HASH_KEY']), raw.encode(), hashlib.sha256).hexdigest()


async def lookup_session(request):
    raw = request.cookies.get(COOKIE, '')
    if not raw or len(raw) > 128:
        return None
    return await db.sessions.find_one({'token_hash': digest(raw), 'expires_at': {'$gt': utcnow()}}, {'_id': 0})


async def owner(request: Request, _=Depends(same_origin)):
    session = await lookup_session(request)
    if not session:
        raise HTTPException(401, 'Przestrzeń wygasła. Otwórz panel ponownie.')
    return session


class WorkspaceStatus(BaseModel):
    ready: bool
    expires_at: str


@router.post('/session', response_model=WorkspaceStatus, dependencies=[Depends(same_origin)])
async def establish(request: Request, response: Response):
    session = await lookup_session(request)
    if not session:
        raw = secrets.token_urlsafe(32)
        ttl = int(os.environ['SESSION_TTL_SECONDS'])
        session = {'id': str(uuid4()), 'token_hash': digest(raw),
                   'expires_at': utcnow() + timedelta(seconds=ttl)}
        await db.sessions.insert_one(dict(session))
        response.set_cookie(COOKIE, raw, httponly=True, secure=True, samesite='lax', path='/', max_age=ttl)
    return WorkspaceStatus(ready=True, expires_at=session['expires_at'].isoformat())


@router.delete('')
async def erase(response: Response, session=Depends(owner)):
    for collection in ['schedules', 'templates', 'groups']:
        await db[collection].delete_many({'owner_id': session['id']})
    await db.sessions.delete_one({'id': session['id']})
    response.delete_cookie(COOKIE, path='/', secure=True, httponly=True, samesite='lax')
    return {'deleted': True}