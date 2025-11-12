# ---- Frontend build stage ----
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci --legacy-peer-deps
COPY frontend ./
RUN npm run build

# ---- Backend runtime ----
FROM python:3.11-slim AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r backend/requirements.txt
COPY backend ./backend
COPY --from=frontend-builder /app/frontend/dist ./frontend_dist
ENV PYTHONPATH=/app/backend \
    FRONTEND_DIST=/app/frontend_dist \
    HOST=0.0.0.0 \
    PORT=8000
WORKDIR /app/backend
EXPOSE 8000
CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
