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

CODE_INPUT_MODULE_DIR = WEB_FRONTEND_DIR/"code_input_module"
ANALYSIS_CONFIGURATION_MODULE_DIR = WEB_FRONTEND_DIR/"analysis_configuration_module"
REQUEST_BUILDER_DIR = WEB_FRONTEND_DIR/"request_builder"
API_CLIENT_DIR = WEB_FRONTEND_DIR/"api_client"
RESULTS_DASHBOARD_DIR = WEB_FRONTEND_DIR/"results_dashboard"
EXPLANATION_VIEW_DIR = WEB_FRONTEND_DIR/"explanation_view"
SCENARIO_VISUALIZER_DIR = WEB_FRONTEND_DIR/"scenario_visualizer"

app=FastAPI(title="TraceVisualizer",
            description="Web interface for concurrent Java code analysis and scenario visualization.",
            version="0.1.0",)

app.mount("/static",StaticFiles(directory=str(STATIC_DIR)),name="static")
app.mount("/code_input_module", StaticFiles(directory=str(CODE_INPUT_MODULE_DIR)),name="code_input_module")
app.mount("/analysis_configuration_module",StaticFiles(directory=str(ANALYSIS_CONFIGURATION_MODULE_DIR)),name="analysis_configuration_module")
app.mount("/request_builder",StaticFiles(directory=str(REQUEST_BUILDER_DIR)),name="request_builder")
app.mount("/api_client", StaticFiles(directory=str(API_CLIENT_DIR)), name="api_client")
app.mount("/results_dashboard", StaticFiles(directory=str(RESULTS_DASHBOARD_DIR)), name="results_dashboard")
app.mount("/explanation_view", StaticFiles(directory=str(EXPLANATION_VIEW_DIR)), name="explanation_view")
app.mount("/scenario_visualizer", StaticFiles(directory=str(SCENARIO_VISUALIZER_DIR)), name="scenario_visualizer")

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