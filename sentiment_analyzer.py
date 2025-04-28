# sentiment_analyzer.py
import os
import redis
from dotenv import load_dotenv
from llama_index.llms.azure_openai import AzureOpenAI
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.chat_engine import SimpleChatEngine
import json
import asyncio  # Make sure asyncio is imported if not already

load_dotenv()

llm = AzureOpenAI(
    model="gpt-4o-mini",
    deployment_name="gpt-4o-mini",
    api_key=os.getenv("AZURE_API_KEY"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_version=os.getenv("AZURE_API_VERSION"),
)

embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

chat_engine = SimpleChatEngine.from_defaults(llm=llm, system_prompt="You are a sentiment analysis bot. Please analyze the sentiment of the following messages seperated by comma and respond with overall sentiment and a score from 1 to 10 for all messages, where 1 is very negative and 10 is very positive. please also give a summary of topics being disucssed and what you predict will be said next (output as json only)")

Settings.llm = llm
Settings.embed_model = embed_model
Settings.chunk_size = 384
Settings.chunk_overlap = 50

REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_STREAM_NAME = os.environ.get("REDIS_STREAM_NAME", "youtube_live_chat_stream")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

async def process_messages(messages_string: str):
    """Analyzes the sentiment of a string of messages."""
    try:
        response = await chat_engine.achat(messages_string)
        return json.loads(response.response)
    except Exception as e:
        print(f"Error processing messages: {e}")
        return {"error": str(e)}

async def consume_stream(results_queue: asyncio.Queue):  # <--- ADD results_queue AS AN ARGUMENT HERE
    """Consumes messages from the Redis stream and puts the analysis results in a queue."""
    last_id = '0'

    while True:
        try:
            messages = redis_client.xread(
                streams={REDIS_STREAM_NAME: last_id},
                count=5,
                block=8000,
            )

            if messages:
                stream_name, message_list = messages[0]
                all_messages_text = " ".join([data.get('message', ',') for _, data in message_list])
                # print(f"[CONSUMER] Received messages: {all_messages_text}")
                if all_messages_text:
                    analysis_result = await process_messages(all_messages_text)
                    print(f"[CONSUMER] About to put in queue: {analysis_result}")
                    await results_queue.put(analysis_result)
                    print(f"[CONSUMER] Put in queue.")
                    for message_id, _ in message_list:
                        last_id = message_id
            else:
                print("[CONSUMER] No new messages received...")

            await asyncio.sleep(0.1)

        except redis.exceptions.ConnectionError as e:
            print(f"[CONSUMER] Error connecting to Redis: {e}")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[CONSUMER] An error occurred: {e}")
            await asyncio.sleep(5)

async def main_consumer(results_queue: asyncio.Queue):
    await consume_stream(results_queue)

if __name__ == "__main__":
    results_queue = asyncio.Queue()
    asyncio.run(main_consumer(results_queue))