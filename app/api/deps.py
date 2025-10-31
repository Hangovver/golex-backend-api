from typing import Generator
from ..db.session import SessionLocal

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Export SessionLocal for backwards compatibility
__all__ = ["get_db", "SessionLocal"]
