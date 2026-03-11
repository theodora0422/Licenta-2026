from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend_analysis_service.api_layer.analysis_controller import router as analysis_router

BASE_DIR=Path(__file__).resolve().parent
WEB_FRONTEND_DIR=BASE_DIR/"web_frontend"
STATIC_DIR=WEB_FRONTEND_DIR/"static"
TEMPLATES_DIR=WEB_FRONTEND_DIR/"templates"

app=FastAPI(title="TraceVisualizer",
            description="Web interface for concurrent Java code analysis and scenario visualization.",
            version="0.1.0",)

app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")
templates=Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/",response_class=HTMLResponse)
async def home(request:Request)->HTMLResponse:
    return templates.TemplateResponse(
        "index.html",
        {"request":request, "page_title":"Trace Visualizer"},
    )
app.include_router(analysis_router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)