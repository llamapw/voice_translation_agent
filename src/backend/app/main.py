from typing import Dict

from fastapi import FastAPI


app = FastAPI(title="voice_translation_agent")


@app.get("/health")
def read_health() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "voice_translation_agent",
    }
