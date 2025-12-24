from fastapi import FastAPI, Depends, Request
from auth import get_current_user
from limiter import limiter
from config import settings
from database import engine, Base
app = FastAPI(title="Rate Limited API")

@app.on_event("startup")
async def startup():
    # ensure db tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # runs for every request
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    # welcome message
    return {
        "message": "Welcome to the Rate Limited API. Use /secure-data with X-API-Token header."
    }

@app.get("/secure-data")
async def secure_data(
    user_id: str = Depends(get_current_user)
):
    """
    protected endpoint example. checks limit before returning data.
    """
    await limiter.check_limit(user_id)

    return {
        "user": user_id,
        "data": "This is secured data",
        "limits": {
            "per_minute": 5,
            "per_day": 100
        }
    }

