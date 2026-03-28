FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download VADER lexicon so the container doesn't need outbound access at runtime
RUN python -c "import nltk; nltk.download('vader_lexicon', quiet=True)"

COPY . .

CMD ["python", "-m", "bot.main"]
