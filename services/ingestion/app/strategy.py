from app.parsers.sqlite_parser import SQLiteParser
from app.models import IngestionResponse

class Ingestor:
    def __init__(self):
        self.parsers = {
            "sqlite": SQLiteParser(),
            #"json": SQLiteParser(),        #TODO: not implemented yet
            #"postgres": SQLiteParser(),    #TODO: not implemented yet
        }

    async def process_schema(self, source_type: str, data: str) -> IngestionResponse:
        parser = self.parsers.get(source_type)
        if not parser:
            raise ValueError(f"Unsupported input type: {source_type}")
        
        tables = parser.parse(data)
        
        return IngestionResponse(tables=tables)