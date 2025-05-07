from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kubernetes_ai_ops_agent_provider import KubernetesAIOpsAgentProvider

logging.basicConfig(level=logging.INFO)

agent_provider = KubernetesAIOpsAgentProvider()


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with agent_provider:  # AgentProvider handles its own stack
        logging.info("Kubernetes AI‑Ops agent ready")
        yield  # application is live
        # teardown handled by provider


app = FastAPI(lifespan=lifespan)


@app.get("/healthz")
async def health() -> dict[str, str]:
    return {"status": "ok"}


# Mount Chainlit after app creation (lazy import avoids heavy deps during cold start)
from chainlit.utils import mount_chainlit

mount_chainlit(app=app, target="chat.py", path="/chat")
