
from sqlalchemy import Column, Integer, String, BigInteger
from database import Base

class RateLimitUsage(Base):
    __tablename__ = "rate_limit_usage"

    # tracks request count per user per window
    user_id = Column(String, primary_key=True, index=True)
    window_key = Column(String, primary_key=True, index=True) 
    request_count = Column(Integer, default=0)
    
class BlockedUser(Base):
    __tablename__ = "blocked_users"

    # tracks abusive users and block expiration
    user_id = Column(String, primary_key=True, index=True)
    blocked_until = Column(BigInteger)  
    violation_count = Column(Integer, default=0)

