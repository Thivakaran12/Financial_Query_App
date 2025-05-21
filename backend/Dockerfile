FROM python:3.11-slim AS builder
WORKDIR /app

# copy only requirements 
COPY requirements.txt .

RUN pip install --user --upgrade pip \
 && pip install --user -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# bring in installed libraries
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# copy source (everything in this folder)
COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# adjust to your invocation
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

