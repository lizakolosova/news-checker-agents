from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv(override=True)

from news_fact_checker.api.routes import router

app = FastAPI(
    title="Multi-Agent News Fact Checker",
    description="Collaborative multi-agent system for fact-checking news articles",
    version="1.0",
    debug=True,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "news_fact_checker.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )