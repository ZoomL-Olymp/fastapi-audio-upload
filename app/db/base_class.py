from sqlalchemy.orm import DeclarativeBase
from typing import Any

class Base(DeclarativeBase):
    id: Any # Placeholder for type checkers