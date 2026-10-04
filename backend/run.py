import uvicorn
from fastapi import FastAPI
from careerlens.ingest.router import router as ingest_router

app = FastAPI(title="CareerLens API")

app.include_router(ingest_router)

@app.get("/")
def root():
    return {"message": "Welcome to CareerLens API"}

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
