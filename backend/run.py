import uvicorn
from fastapi import FastAPI
from careerlens.ingest.router import router as ingest_router
from careerlens.nlp.router import router as nlp_router

app = FastAPI(title="CareerLens API - NLP & Parsing Service")

# Include routers
app.include_router(ingest_router)
app.include_router(nlp_router)

@app.get("/")
def root():
    return {"message": "Welcome to CareerLens API - Ingestion & NLP Services"}

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=8000, reload=True)
