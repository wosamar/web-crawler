from fastapi import FastAPI
from starlette.staticfiles import StaticFiles
from api.routers.api import router as api_router
from api.routers.api_html import router as api_html_router
import uvicorn
from definition import BASEDIR

app = FastAPI()

app.include_router(api_router)
app.include_router(api_html_router)
app.mount("/static", StaticFiles(directory=BASEDIR/"api"/"routers"/"static"), name="static")

def run():
    uvicorn.run(app, host="127.0.0.1", port=8080)

if __name__ == "__main__":
    run()
