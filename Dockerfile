FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV API_URL=http://127.0.0.1:8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY iidatech ./iidatech
COPY streamlit_app.py learning_engine.py market_modeling.py chroma_config.py country_industry_packs.py ./
RUN mkdir -p opportunity_workspaces business_build_outputs

COPY web/package.json web/package-lock.json ./web/
RUN cd web && npm ci --include=dev
COPY web ./web
RUN cd web && API_URL=http://127.0.0.1:8000 npm run build

COPY scripts/render-combined-start.sh /start.sh
RUN chmod +x /start.sh

ENV NODE_ENV=production
EXPOSE 3000
CMD ["/start.sh"]