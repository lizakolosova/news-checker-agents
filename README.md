Multi-Agent News Fact Checker
=============================

Production-ready fact-checking system with 4-agent pipeline (Claim → Research → Evidence → Verdict)

Prerequisites:
- Python 3.8+
- Node.js + npm
- Serper API key (required): https://serper.dev
- Groq/OpenAI keys (optional)

QUICK START
==============

1. BACKEND (FastAPI)
-------------------
From project root:

python -m venv .venv
.\.venv\Scripts\activate  # Windows PowerShell

pip install -r requirements.txt

# Set API keys (PowerShell)
$env:SERPER_API_KEY="your_serper_key"

$env:GROQ_API_KEY="your_groq_key"  # optional

# Run backend
uvicorn news_fact_checker.api.main:app --reload

Backend: http://localhost:8000/docs

2. FRONTEND (React + Vite)
-------------------------
cd frontend

npm install

npm run dev

Frontend: http://localhost:5173 (or 5174 if busy)

3. TEST IT
----------
1. Open frontend → Paste news article
2. Set max claims → Click "Fact Check" 
3. See real-time verdicts + sources!

PROJECT STRUCTURE
===================

```
multi-agents-project/
├── news_fact_checker/          # FastAPI backend + agents
│   ├── api/                    # FastAPI routes + CORS
│   ├── claim_extraction/       # Agent 1: Extract Claims
│   ├── evidence/               # Agent 2: Evaluate credibility
│   ├── research/               # Agent 3: Serper API search
│   └── verdict/                # Agent4: Final verdicts 
├── frontend/                   # React + Vite UI
├── tests/                      # pytest 
├── requirements.txt
└── README.md  ← This file
```

AGENTS PIPELINE
===============

1. CLAIM EXTRACTION → Finds verifiable facts (numbers, dates, stats)
2. RESEARCH AGENT  → Serper API searches (.gov, news first)
3. EVIDENCE EVAL   → Scores credibility + consensus
4. VERDICT        → TRUE/FALSE/MOSTLY_TRUE + sources

EXAMPLE OUTPUT:
Claim: "Eurostat: 2.9% inflation Dec 2023"
Verdict: TRUE (87% confidence)
Sources: Eurostat PDF, Reuters, ECB

TROUBLESHOOTING
=================

Port busy (5173):  Vite auto-changes to 5174+

No verdicts:       Verify SERPER_API_KEY

Backend silent:    Check http://localhost:8000/docs

RUN TESTS
===========

pytest tests/ -v


