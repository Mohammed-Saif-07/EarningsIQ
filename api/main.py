from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.health import router as health_router
from api.routes.qa import router as qa_router
from api.routes.sentiment import router as sentiment_router
from api.routes.signals import router as signals_router
from api.routes.transcripts import router as transcripts_router
from api.websocket import router as websocket_router

app = FastAPI(title="EarningsIQ", description="What CFOs say, what the market misses.", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(transcripts_router)
app.include_router(sentiment_router)
app.include_router(signals_router)
app.include_router(qa_router)
app.include_router(websocket_router)


@app.get("/")
def root() -> dict:
    return {
        "project": "EarningsIQ - Earnings Call Intelligence Engine",
        "tagline": "What CFOs say, what the market misses.",
        "built_by": "Saif Mohammed",
        "contact": "smohammed8@seattleu.edu",
        "github": "github.com/Mohammed-Saif-07",
        "docs": "/docs",
    }
