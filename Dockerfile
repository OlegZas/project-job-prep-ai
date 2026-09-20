FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8501 \
    DATAPREP_ANALYTICS_MODE=session

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY src ./src
COPY docs ./docs
COPY evals ./evals
COPY sample_data ./sample_data
COPY warehouse ./warehouse

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=3)"

CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT}"]
