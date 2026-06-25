FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN mkdir -p data media_cache logs
EXPOSE 8000 8501
CMD ["python", "-m", "xnative.sample_pipeline"]
