from flask import Flask, jsonify, render_template
import asyncio
import threading
from sentiment_analyzer import consume_stream  # Import process_messages if you need it here
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app)
results_queue = asyncio.Queue()
latest_result = {}
is_running = False  # Flag to track if the background task is running

async def update_latest_result():
    """Continuously gets the latest result from the queue."""
    while True:
        result = await results_queue.get()
        global latest_result
        latest_result = result
        print(f"[API] Updated latest_result: {latest_result}")  # For debugging
        await asyncio.sleep(0.1) # Be a good async citizen

async def main():
    """Runs the consumer and updater concurrently within the same event loop."""
    await asyncio.gather(consume_stream(results_queue), update_latest_result())

def run_background_tasks():
    """Runs the asyncio tasks in a separate thread."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())

@app.route('/api/start', methods=['GET'])
@cross_origin()
def start_sentiment():
    """API endpoint to start the sentiment analysis process."""
    global is_running
    if not is_running:
        threading.Thread(target=run_background_tasks, daemon=True).start()
        is_running = True
        return jsonify({"message": "Sentiment analysis started"})
    else:
        return jsonify({"message": "Sentiment analysis already running"})

@app.route('/api/sentiment', methods=['GET'])
@cross_origin()
def get_sentiment():
    """API endpoint to get the latest sentiment analysis result."""
    return jsonify(latest_result)

@app.route('/')
def index():
    return "Sentiment Analysis API is running. Access /api/sentiment for results."

if __name__ == "__main__":
    print("Starting Flask app...")
    app.run(debug=True, use_reloader=False)