from abc import ABC, abstractmethod
from sqlalchemy.orm import sessionmaker, Session
from utils.miscellaneous.decorators import singleton


class BaseEngine(ABC):

    @abstractmethod
    def create_engine(self):
        pass

    @property
    def engine(self):
        return self._engine

    @engine.setter
    def engine(self, engine):
        self._engine = self.create_engine(engine) if isinstance(engine, str) else engine

    @property
    def collation(self) -> str:
        return self._collation

    @collation.setter
    def collation(self, collation):
        self._collation = collation

    @property
    def dialect(self):
        return self.engine.dialect

    @property
    def session(self) -> Session:
        return self()

    def __call__(self, *args, **kwargs) -> Session:
        return self.SessionWrapper(self._session(*args, **kwargs))

    @session.setter
    def session(self, engine):
        self._session = sessionmaker(
            bind=engine if engine else self.engine,
            expire_on_commit=self.expire_on_commit
      )

    class SessionWrapper:
        def __init__(self, session: Session):
            self._session = session

        def __getattr__(self, name):
            return getattr(self._session, name)

        def __enter__(self):
            return self._session

        def __exit__(self, exc_type, exc_val, exc_tb):
            self._session.close()
