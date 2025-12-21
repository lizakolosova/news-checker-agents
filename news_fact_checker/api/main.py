from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from news_fact_checker.api.routes import router

app = FastAPI(
    title="Multi-Agent News Fact Checker",
    description="Collaborative multi-agent system for fact-checking news articles",
    version="1.0",
    debug=True
)
app.include_router(router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)