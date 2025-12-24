
from sqlalchemy import Column, Integer, String, BigInteger
from database import Base

class RateLimitUsage(Base):
    __tablename__ = "rate_limit_usage"

    # This table tracks how many requests a user made in a specific window.
    # user_id: "user123"
    # window_key: "min:29443135" (unique for that minute) or "day:20251224"
    # request_count: The number of requests (e.g., 5)
    user_id = Column(String, primary_key=True, index=True)
    window_key = Column(String, primary_key=True, index=True) 
    request_count = Column(Integer, default=0)
    
class BlockedUser(Base):
    __tablename__ = "blocked_users"

    # This table tracks "bad behavior".
    # violation_count: How many times they hit the limit.
    # blocked_until: A timestamp (e.g. 1766588874). If current time < this, they are blocked.
    user_id = Column(String, primary_key=True, index=True)
    blocked_until = Column(BigInteger) 
    violation_count = Column(Integer, default=0)

