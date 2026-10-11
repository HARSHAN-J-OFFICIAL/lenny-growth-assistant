"""
Aggregated API Version 1 Router.
"""

from fastapi import APIRouter
from .endpoints import artifacts, chat, health, knowledge, providers, retrieval, sessions, skills

api_v1_router = APIRouter()

# Diagnostics & Health Check
api_v1_router.include_router(health.router, tags=["Health"])

# AI Providers & Model Configuration
api_v1_router.include_router(providers.router, prefix="/providers", tags=["Providers"])

# Specialized Writing Skills (Ship 30 for 30)
api_v1_router.include_router(skills.router, prefix="/skills", tags=["Skills"])

# Knowledge Base & Retrieval
api_v1_router.include_router(retrieval.router, prefix="/retrieval", tags=["Retrieval"])
api_v1_router.include_router(knowledge.router, prefix="/knowledge", tags=["Knowledge"])

# Multi-Session & History Persistence (PostgreSQL)
api_v1_router.include_router(sessions.router, prefix="/sessions", tags=["Sessions"])

# Grounded RAG Chat Completion
api_v1_router.include_router(chat.router, prefix="/chat", tags=["Chat"])

# Sandboxed Artifact Viewer
api_v1_router.include_router(artifacts.router, prefix="/artifacts", tags=["Artifacts"])
