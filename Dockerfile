FROM python:3.9-slim-buster

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt --no-cache-dir

COPY live_chat_scraper.py .

CMD ["python", "live_chat_scraper.py"]