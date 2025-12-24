
import time
from fastapi import HTTPException
from sqlalchemy.future import select
from sqlalchemy import update, delete
from database import AsyncSessionLocal
from models import RateLimitUsage, BlockedUser
from config import settings

class RateLimiter:
    async def check_limit(self, user_id: str):
        # db session for checking limits
        async with AsyncSessionLocal() as session:
            now = int(time.time())
            
            # 1. check if user is blocked
            stmt = select(BlockedUser).where(BlockedUser.user_id == user_id)
            result = await session.execute(stmt)
            blocked_entry = result.scalar_one_or_none()

            if blocked_entry:
                print(f"DEBUG: Found block entry for {user_id}. Until: {blocked_entry.blocked_until}. Now: {now}")
                
                # reject if currently blocked
                if blocked_entry.blocked_until > 0 and now < blocked_entry.blocked_until:
                    raise HTTPException(status_code=403, detail="User is blocked due to abuse.")
                
                # clean up expired block
                elif blocked_entry.blocked_until > 0 and now >= blocked_entry.blocked_until:
                     await session.delete(blocked_entry)
                     await session.commit()

            # 2. generate time keys (minute & day)
            min_window = now // 60
            day_window = time.strftime("%Y%m%d")
            
            min_key = f"min:{min_window}"
            day_key = f"day:{day_window}"

            # 3. check minute limit
            stmt = select(RateLimitUsage).where(
                RateLimitUsage.user_id == user_id, 
                RateLimitUsage.window_key == min_key
            )
            result = await session.execute(stmt)
            usage_min = result.scalar_one_or_none()

            if not usage_min:
                # new minute entry
                usage_min = RateLimitUsage(user_id=user_id, window_key=min_key, request_count=1)
                session.add(usage_min)
            else:
                # check max requests
                if usage_min.request_count >= settings.RATE_LIMIT_PER_MINUTE:
                    await self._record_abuse(session, user_id, now)
                    raise HTTPException(status_code=429, detail="Minute limit exceeded")
                
                usage_min.request_count += 1
            
            # 4. check day limit
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
            
            await session.commit()

    async def _record_abuse(self, session, user_id: str, now: int):
        """
        records violation. blocks user if threshold reached.
        """
        stmt = select(BlockedUser).where(BlockedUser.user_id == user_id)
        result = await session.execute(stmt)
        blocked_entry = result.scalar_one_or_none()

        if not blocked_entry:
            # start tracking violations
            blocked_entry = BlockedUser(user_id=user_id, violation_count=1, blocked_until=0)
            session.add(blocked_entry)
        else:
            blocked_entry.violation_count += 1
        
        # block if too many violations
        if blocked_entry.violation_count >= settings.ABUSE_THRESHOLD:
            print(f"BLOCKING USER {user_id} until {now + settings.BLOCK_DURATION_SECONDS}")
            blocked_entry.blocked_until = now + settings.BLOCK_DURATION_SECONDS
        else:
             print(f"User {user_id} violation count: {blocked_entry.violation_count}")
        
        await session.commit()


limiter = RateLimiter()
