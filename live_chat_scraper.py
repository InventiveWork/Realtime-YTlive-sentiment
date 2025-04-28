import asyncio
import json
import os
import redis
import pytchat
from dotenv import load_dotenv


load_dotenv()

YOUTUBE_LIVE_URL = os.environ.get("YOUTUBE_LIVE_URL")
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_STREAM_NAME = os.environ.get("REDIS_STREAM_NAME", "youtube_live_chat_stream")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

def process_chat_messages(chat):
    while chat.is_alive():
        for message in chat.get().sync_items():
            author = message.author.name
            text = message.message
            timestamp = message.timestamp / 1000  # Convert milliseconds to seconds
            payload = {'author': author, 'message': text, 'timestamp': timestamp}
            print(f"Author: {author}, Message: {text}, Timestamp: {timestamp}")
            try:
                redis_client.xadd(REDIS_STREAM_NAME, payload)
                print(f"Published to Redis: {payload}")
            except redis.exceptions.ConnectionError as e:
                print(f"Error connecting to Redis: {e}")
            except Exception as e:
                print(f"Error publishing to Redis: {e}")

async def main():
    if not YOUTUBE_LIVE_URL:
        print("Please set the YOUTUBE_LIVE_URL environment variable.")
        return

    try:
        chat = pytchat.create(video_id=YOUTUBE_LIVE_URL)
        process_chat_messages(chat)
    except Exception as e:
        print(f"Error during live chat extraction: {e}")

if __name__ == "__main__":
    asyncio.run(main())