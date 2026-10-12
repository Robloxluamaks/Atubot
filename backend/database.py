import os
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.environ['MONGO_URL'], tz_aware=True)
db = client[os.environ['DB_NAME']]


def utcnow():
    return datetime.now(timezone.utc)


async def setup_indexes():
    for name in ['sessions', 'templates', 'groups', 'schedules', 'cron_runs']:
        collection = db[name]
        await collection.create_index('expires_at', expireAfterSeconds=0)
        if name != 'cron_runs':
            await collection.create_index('id', unique=True)
    await db.sessions.create_index('token_hash', unique=True)
    await db.schedules.create_index([('state', 1), ('next_run', 1)])
    for name in ['templates', 'groups', 'schedules']:
        await db[name].create_index('owner_id')