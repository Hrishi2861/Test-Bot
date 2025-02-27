import logging
from pymongo import MongoClient
from config import MONGO_URI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = MongoClient(MONGO_URI)
db = client["rclone_bot"]
configs_collection = db["rclone_configs"]

async def store_rclone_config(user_id, file_path):
    try:
        with open(file_path, "r") as f:
            config_data = f.read()
        configs_collection.update_one({"user_id": user_id}, {"$set": {"config": config_data}}, upsert=True)
        logger.info(f"Stored Rclone config for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to store Rclone config for user {user_id}: {e}")

async def get_rclone_config(user_id):
    try:
        config = configs_collection.find_one({"user_id": user_id})
        if config:
            return config.get("config")
        return None
    except Exception as e:
        logger.error(f"Failed to retrieve Rclone config for user {user_id}: {e}")
        return None
