FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir aiogram==3.6.0 aiohttp==3.9.5

COPY bot.py .

CMD ["python", "bot.py"]
