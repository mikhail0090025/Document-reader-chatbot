from sqlalchemy import text

from .session import engine
from .base import Base

from . import models



def init_database():

    with engine.connect() as conn:

        conn.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS vector"
            )
        )

        conn.commit()


    Base.metadata.create_all(
        engine
    )