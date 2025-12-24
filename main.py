from fastapi import FastAPI, Depends, Request
from auth import get_current_user
from limiter import limiter
from config import settings
from database import engine, Base
app = FastAPI(title="Rate Limited API")

@app.on_event("startup")
async def startup():
    # When the app starts, we want to make sure our database tables exist.
    # This creates the 'rate_limit_usage' and 'blocked_users' tables if they aren't there.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    # This runs for every request.
    response = await call_next(request)
    return response

@app.get("/")
async def root():
    # Simple welcome message to let us know the API is running.
    return {
        "message": "Welcome to the Rate Limited API. Use /secure-data with X-API-Token header."
    }

@app.get("/secure-data")
async def secure_data(
    user_id: str = Depends(get_current_user)
):
    """
    This is an example of a protected endpoint.
    Before we return the data, we ask the limiter: "Is this user allowed?"
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

