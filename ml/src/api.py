"""
ML Service API for model inference.
"""

from fastapi import FastAPI
from datetime import datetime

app = FastAPI(
    title="PEA RE Forecast - ML Service",
    description="Machine Learning inference service",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "ml-service",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/models")
async def list_models():
    """List available models."""
    return {
        "models": [
            {
                "name": "solar-forecast",
                "version": "mock-v0.1.0",
                "type": "xgboost",
                "status": "not_trained",
            },
            {
                "name": "voltage-prediction",
                "version": "mock-v0.1.0",
                "type": "neural_network",
                "status": "not_trained",
            },
        ]
    }
