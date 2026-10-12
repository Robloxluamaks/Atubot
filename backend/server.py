import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.middleware.cors import CORSMiddleware

load_dotenv(Path(__file__).parent / '.env')

from discord_routes import router  # noqa: E402

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]


@asynccontextmanager
async def lifespan(app):
    yield
    client.close()


app = FastAPI(title='Relay — Discord AutoSender', lifespan=lifespan)
app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ['CORS_ORIGINS'].split(','),
    allow_credentials=False,
    allow_methods=['GET', 'POST'],
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
    return JSONResponse(status_code=422, content={
        'detail': 'Sprawdź token, identyfikatory kanałów i treść (1–2000 znaków).',
        'fields': ['.'.join(str(v) for v in error['loc'][1:]) for error in exc.errors()],
    })


@app.get('/api/health')
async def health():
    return {'status': 'ok', 'service': 'relay'}


logging.basicConfig(level=logging.INFO)
logging.getLogger('httpx').setLevel(logging.WARNING)
logging.getLogger('httpcore').setLevel(logging.WARNING)