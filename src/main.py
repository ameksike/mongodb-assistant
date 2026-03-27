import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from src.controllers.workflowController import router as workflowRouter

load_dotenv(dotenv_path="cfg/.env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="Conversational Assistance System",
    description="Dynamic conversational interactions guided by workflow definitions.",
    version="1.0.0",
)

app.include_router(workflowRouter)


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}
