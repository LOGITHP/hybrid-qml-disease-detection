import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User

async def main():
    client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    db = client["hybrid_qml_db"]
    await init_beanie(database=db, document_models=[Dataset, DatasetVersion, User])
    
    datasets = await Dataset.find_all().to_list()
    print(f"Total datasets before cleanup: {len(datasets)}")
    
    # Keep the first one, delete the rest
    if len(datasets) > 1:
        for d in datasets[1:]:
            await DatasetVersion.find(DatasetVersion.dataset_id == str(d.id)).delete()
            await d.delete()
            print(f"Deleted {d.id}")
            
    print("Cleanup complete.")

if __name__ == "__main__":
    asyncio.run(main())
