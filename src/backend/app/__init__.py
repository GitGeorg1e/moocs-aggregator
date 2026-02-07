"""
MOOCs Aggregator – FastAPI backend application.

Package layout
--------------
api/          HTTP endpoints (versioned under ``api/v1/``)
connectors/   Platform scrapers (Coursera, MIT OCW, …)
core/         App-wide config and database session
models/       SQLAlchemy ORM models
schemas/      Pydantic request / response models
scripts/      CLI sync scripts
services/     Business-logic layer
"""
