from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from src.orchestrator.orchestrator import Orchestrator
import os, json

app = FastAPI(title="Research Companion API")
app.mount('/static', StaticFiles(directory=os.path.join(os.path.dirname(__file__),'..','ui','static')), name='static')
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__),'..','ui','templates'))
orc = Orchestrator(tmp_dir=os.getenv('CACHE_DIR','./artifacts'))

class QueryRequest(BaseModel):
    query: str
    max_results: int = 3

@app.get('/', response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})

@app.post('/query', response_class=JSONResponse)
async def run_query(req: QueryRequest):
    result = orc.run(query=req.query, max_results=req.max_results)
    return JSONResponse(result)
