
class Settings:
    RATE_LIMIT_PER_MINUTE: int = 10
    RATE_LIMIT_PER_DAY: int = 1000
    BLOCK_DURATION_SECONDS: int = 600  # 10 minutes
    ABUSE_THRESHOLD: int = 5

settings = Settings()
