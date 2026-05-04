from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
templates = Jinja2Templates(directory="../templates")
app.mount("/static", StaticFiles(directory="../static"), name="static")


@app.get("/")
async def selection_page(request: Request):
    pass


@app.post("/selection")
async def select_type(request: Request):
    pass


@app.get("/result")
async def get_result(request: Request):
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)