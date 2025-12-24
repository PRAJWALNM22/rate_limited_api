from fastapi import Header, HTTPException

async def get_current_user(x_api_token: str = Header(...)):
    # This is our simple gatekeeper.
    # It just checks if the 'X-API-Token' header is present.
    # In a real app, we would check if this token exists in a database.
    if not x_api_token:
        raise HTTPException(status_code=401, detail="Missing API token")
    return x_api_token
