
import time
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import AsyncSessionLocal
from models import RateLimitUsage, BlockedUser
from config import settings

class RateLimiter:
    async def check_limit(self, user_id: str):
        # We start a database session to check and update the user's limits.
        async with AsyncSessionLocal() as session:
            now = int(time.time())
            
            # Step 1: First, we check if this user is currently in the "penalty box" (blocked).
            stmt = select(BlockedUser).where(BlockedUser.user_id == user_id)
            result = await session.execute(stmt)
            blocked_entry = result.scalar_one_or_none()

            if blocked_entry:
                print(f"DEBUG: Found block entry for {user_id}. Until: {blocked_entry.blocked_until}. Now: {now}")
                
                # If they are blocked and the time hasn't passed yet, reject them.
                if blocked_entry.blocked_until > 0 and now < blocked_entry.blocked_until:
                    raise HTTPException(status_code=403, detail="User is blocked due to abuse.")
                
                # If the block time has passed, or it was just a warning record (0), clean it up.
                elif blocked_entry.blocked_until > 0 and now >= blocked_entry.blocked_until:
                     await session.delete(blocked_entry)
                     await session.commit()
                # If blocked_until is 0, it means we are just tracking violations but haven't blocked them yet.

            # Step 2: Calculate the "Window Keys".
            # 'min_window' changes every minute (e.g., 29443135 -> 29443136).
            # 'day_window' changes every day (e.g., 20251224).
            min_window = now // 60
            day_window = time.strftime("%Y%m%d")
            
            min_key = f"min:{min_window}"
            day_key = f"day:{day_window}"

            # Step 3: Check the "Minute Limit".
            # We look for a record for THIS user in THIS specific minute.
            stmt = select(RateLimitUsage).where(
                RateLimitUsage.user_id == user_id, 
                RateLimitUsage.window_key == min_key
            )
            result = await session.execute(stmt)
            usage_min = result.scalar_one_or_none()

            if not usage_min:
                # First request this minute? Create a new record.
                usage_min = RateLimitUsage(user_id=user_id, window_key=min_key, request_count=1)
                session.add(usage_min)
            else:
                # Already exists? Check if they hit the max.
                if usage_min.request_count >= settings.RATE_LIMIT_PER_MINUTE:
                    # They went over! Record this as "abuse" and reject them.
                    await self._record_abuse(session, user_id, now)
                    raise HTTPException(status_code=429, detail="Minute limit exceeded")
                
                # Otherwise, just count this request.
                usage_min.request_count += 1
            
            # Step 4: Check the "Day Limit" (Same logic as above, but for the day key).
            stmt = select(RateLimitUsage).where(
                RateLimitUsage.user_id == user_id, 
                RateLimitUsage.window_key == day_key
            )
            result = await session.execute(stmt)
            usage_day = result.scalar_one_or_none()

            if not usage_day:
                usage_day = RateLimitUsage(user_id=user_id, window_key=day_key, request_count=1)
                session.add(usage_day)
            else:
                if usage_day.request_count >= settings.RATE_LIMIT_PER_DAY:
                     await self._record_abuse(session, user_id, now)
                     raise HTTPException(status_code=429, detail="Day limit exceeded")
                usage_day.request_count += 1
            
            # Save all our changes (the counts) to the database.
            await session.commit()

    async def _record_abuse(self, session, user_id: str, now: int):
        """
        Helper function to track bad behavior. 
        If a user hits a limit, we mark a 'violation'.
        If they do it too many times, we set a future time to block them until.
        """
        stmt = select(BlockedUser).where(BlockedUser.user_id == user_id)
        result = await session.execute(stmt)
        blocked_entry = result.scalar_one_or_none()

        if not blocked_entry:
            # First offense? Start tracking them.
            blocked_entry = BlockedUser(user_id=user_id, violation_count=1, blocked_until=0)
            session.add(blocked_entry)
        else:
            # Repeat offender? Increment the count.
            blocked_entry.violation_count += 1
        
        # Did they cross the line (e.g. 5 violations)?
        if blocked_entry.violation_count >= settings.ABUSE_THRESHOLD:
            print(f"BLOCKING USER {user_id} until {now + settings.BLOCK_DURATION_SECONDS}")
            # Set the "jail time" (current time + 10 minutes).
            blocked_entry.blocked_until = now + settings.BLOCK_DURATION_SECONDS
        else:
             print(f"User {user_id} violation count: {blocked_entry.violation_count}")
        
        await session.commit()


limiter = RateLimiter()
