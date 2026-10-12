import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / '.env')

from discord_routes import router  # noqa: E402
from database import client, db, setup_indexes  # noqa: E402
from workspace_auth import router as workspace_router  # noqa: E402
from library_routes import router as library_router  # noqa: E402
from schedule_routes import router as schedule_router  # noqa: E402
from cron_routes import router as cron_router  # noqa: E402


@asynccontextmanager
async def lifespan(app):
    await setup_indexes()
    yield
    client.close()


app = FastAPI(title='Relay — Discord AutoSender', lifespan=lifespan)
app.include_router(router)
app.include_router(workspace_router)
app.include_router(library_router)
app.include_router(schedule_router)
app.include_router(cron_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ['CORS_ORIGINS'].split(','),
    allow_credentials=True,
    allow_methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    allow_headers=['Content-Type'],
)


@app.middleware('http')
async def privacy_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.exception_handler(RequestValidationError)
async def safe_validation_error(request, exc):
    # Never serialize Pydantic's input field: it can contain a bot token.
    message = 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).'
    if request.url.path.startswith(('/api/library', '/api/schedules')):
        message = 'Sprawdź wymagane pola, datę i limity wiadomości lub embeda.'
    return JSONResponse(status_code=422, content={
        'detail': message,
        'fields': ['.'.join(str(v) for v in error['loc'][1:]) for error in exc.errors()],
    })


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'relay'}


logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)