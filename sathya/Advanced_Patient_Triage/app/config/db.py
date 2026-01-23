from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

# One client for the whole app (recommended)
client = AsyncIOMotorClient(settings.MONGODB_URI)

# Database reference
db = client[settings.MONGODB_DB]

# Collection reference
symptom_collection = db[settings.MONGODB_COLLECTION]
