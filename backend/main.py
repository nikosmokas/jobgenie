from fastapi import FastAPI
from backend.api.routes import router

app = FastAPI(title="JobGenie Unified API")
app.include_router(router)
