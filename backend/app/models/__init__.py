from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import all models so they're registered with Base.metadata
# isort: skip_file
from app.models import knowledge  # noqa: F401
