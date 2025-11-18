import json
import logging
import os
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from server.common import service_name
from server.health_check import check_self, HealthState


# Create FastAPI app
app = FastAPI(
    title=f"{service_name} API",
    version=os.environ.get("APPLICATION_VERSION", "NOT_FOUND")
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

instrumentator = Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app, endpoint="/metrics")


@app.get("/", response_class=HTMLResponse)
def hello():
    observability_links_html = f"""
    <li><a href="https://outshift-preprod.observe.appdynamics.com/ui/tools/logs?since=now-1h">Logs</a> (if deployed to ETI Platform)</li>
    <li><a href='{os.environ.get("METRICS_DASHBOARD_URL")}'>Grafana Dashboard</a> (if deployed to ETI Platform)</li>
    """
    
    return f"""
    <html>
        <body>
        <p>Platform Demo ci-tkf-data-logic-svc Hello World</p>
        <ul>
            <li><a href='/env'>Env Vars</a></li>
            <li><a href='/metrics'>Metrics</a></li>
            <li><a href='/healthz'>Health</a></li>
            <li><a href='/docs'>API Documentation</a></li>
            {observability_links_html}
        </ul>
        </body>
    </html>
    """


@app.get("/env", response_class=HTMLResponse)
def env_var():
    return f"""
    <html>
        <body>
        <p>Platform Demo ci-tkf-data-logic-svc Hello World Environment Vars</p>
        <ul>
            <li>CONFIGMAP_TEST: {os.environ.get("CONFIGMAP_TEST")}</li>
            <li>CONFIGMAP_DEFAULT_EXAMPLE: {os.environ.get("CONFIGMAP_DEFAULT_EXAMPLE")}</li>
            <li>CONFIGMAP_OVERLAY_EXAMPLE: {os.environ.get("CONFIGMAP_OVERLAY_EXAMPLE")}</li>
            <li>APPLICATION_VERSION: {os.environ.get("APPLICATION_VERSION")}</li>
            <li>MOCK_DB_UPTIME: {os.environ.get("MOCK_DB_UPTIME")}</li>
            <li>MOCK_FOO_UPTIME: {os.environ.get("MOCK_FOO_UPTIME")}</li>
        </ul>
        </body>
    </html>
    """


@app.get("/foo", response_class=HTMLResponse)
def foo():
    return """
    <html>
        <body>
        <h1>Hello, foo</h1>
        </body>
    </html>
    """


@app.get("/healthz")
def healthz():
    service_state = check_self()
    
    timestamp = datetime.datetime.now().isoformat()
    response_body = {
        "service_name": service_name,
        "service_state": service_state.name,
        "last_updated": timestamp
    }
    
    # Return appropriate status code for k8s liveness probe
    if (service_state == HealthState.UP) or (service_state == HealthState.DEGRADED):
        return JSONResponse(content=response_body, status_code=200)
    else:
        return JSONResponse(content=response_body, status_code=500)


# Register API routes
from server.api.api import api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))
    
    logger = logging.getLogger(__name__)
    logger.info(f"Starting up the '{service_name}' FastAPI app! Version: '{os.environ.get('APPLICATION_VERSION')}'")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)