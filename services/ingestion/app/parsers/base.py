from abc import ABC, abstractmethod
from typing import List
from shared.models import TableModel

class BaseParser(ABC):
    """
    Base class for all schema parsers.

    Each subclass handles one dialect (e.g. sqlite, postgres)
    and parses raw SQL DDL string into a list of TableModel objects.
    """
    @abstractmethod
    def parse(self, raw_sql: str) -> List[TableModel]:
        """Parse a raw schema string and return list of TableModel objects."""
        pass