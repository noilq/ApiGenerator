from app.clients.ingestor import ingest
from app.clients.normalizer import normalize
from app.clients.generator import generate
from app.clients.exporter import export

async def run_pipeline(request):
    source_type = request.source_type
    schema = await ingest(source_type, request.content)
    normalized = await normalize(source_type, schema["tables"])
    generated = await generate(source_type, normalized["tables"], request.options)
    result = await export(request.options["project_name"] ,generated["files"])
    return result