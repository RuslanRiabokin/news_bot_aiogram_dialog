import logging
from abc import ABC, abstractmethod

logging.basicConfig(level=logging.INFO)

class AbstractDatabase(ABC):
    """Абстрактний клас для роботи з базою даних."""

    @abstractmethod
    async def connect(self):
        pass

    @abstractmethod
    async def disconnect(self):
        pass

    @abstractmethod
    async def execute(self, query: str, params: tuple = ()):
        """Загальний метод для виконання SQL-запитів"""
        pass

    @abstractmethod
    async def fetchone(self, query: str, params: tuple = ()):
        """Отримання одного результату"""
        pass

    @abstractmethod
    async def fetchall(self, query: str, params: tuple = ()):
        """Отримання всіх результатів"""
        pass

    @abstractmethod
    async def create_tables(self):
        """Метод для створення таблиць"""
        pass