FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY rubric.json ./rubric.json

RUN pip install --no-cache-dir .

CMD ["python", "src/cli.py", "--help"]
