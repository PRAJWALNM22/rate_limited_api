from fastapi import Header, HTTPException

async def get_current_user(x_api_token: str = Header(...)):
    # minimal check for token presence
    if not x_api_token:
        raise HTTPException(status_code=401, detail="Missing API token")
    return x_api_token
