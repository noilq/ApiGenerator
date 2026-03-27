from typing import List, Optional
from app.models import GeneratorResponse, TableModel, GeneratorConfig
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
import re

from app.config import get_db_config

import logging
from shared.logging_config import configure_logging
configure_logging()
logger = logging.getLogger(__name__)

class Generator:
    def __init__(self):
        self.templates_dir = "app/templates"
        self.env = Environment(loader=FileSystemLoader(self.templates_dir), trim_blocks=True, lstrip_blocks=True)

        self.env.filters["snake_case"] = self._to_snake_case
        self.env.filters["pascal_case"] = self._to_pascal_case
        self.env.filters["to_python_type"] = self._map_to_python
        self.env.filters["to_sqlalchemy_type"] = self._map_to_sqlalchemy
        self.env.filters["enum_values"] = self._parse_enum_values

    async def generate(self, source_type, data: List[TableModel], options: Optional[dict] = None) -> GeneratorResponse:
        """Render all templates for the given config and return generated files."""
        config = GeneratorConfig(**(options or {}), db_type=source_type)
        db = get_db_config(config.db_type)
        logger.info("Generating project using template path: %s", config.template_path)

        files = await self._render(config.template_path, data, config, db)

        if config.auth.enabled:
            files.update(await self._render(f"shared/{config.language}/auth/{config.auth.strategy}", data, config, db))
            logger.debug("Auth addon rendered: %s", config.auth.strategy)

        if config.ci_cd.enabled:
            files.update(await self._render(f"shared/ci_cd/{config.ci_cd.platform}", data, config, db))
            logger.debug("CI/CD addon rendered: %s", config.ci_cd.platform)

        if config.docker:
            files.update(await self._render("shared/docker", data, config, db))
            logger.debug("Docker addon rendered")

        logger.info("Generation complete, files generated: %d", len(files))
        return GeneratorResponse(files=files, status="success")

    async def _render(self, folder_name: str, data: List[TableModel], config: GeneratorConfig, db: dict) -> dict:
        """
        Render all templates in a folder. Per-table templates (containing 'table' in name)
        are rendered once per table, everything else is rendered once.
        """
        output = {}
        target_dir = Path(self.templates_dir) / folder_name

        if not target_dir.exists():
            logger.debug("Template folder not found, skipping: %s", folder_name)
            return {}

        for template_file in target_dir.rglob("*.jinja2"):
            if "macros" in template_file.parts:  # skip macros definitions
                continue

            rel_path = template_file.relative_to(target_dir)  # always relative to this folder
            jinja_path = template_file.relative_to(Path(self.templates_dir)).as_posix()
            template = self.env.get_template(jinja_path)

            if "table" in template_file.stem:
                for table in data:
                    output_path = str(rel_path).replace("table", self._to_snake_case(table.name)).replace(".jinja2", "")
                    output[output_path] = template.render(
                        table=table, 
                        config=config, 
                        db=db
                    )
                    logger.debug("Rendered: %s -> %s", jinja_path, output_path)
            else:
                output_path = str(rel_path).replace(".jinja2", "")
                output[output_path] = template.render(
                    tables=data, config=config, 
                    db=db
                )
                logger.debug("Rendered: %s -> %s", jinja_path, output_path)

        return output

    # TODO: add _post_process using black or isort idk

    def _map_to_sqlalchemy(self, col) -> str:
        """Map a ColumnModel to its SQLAlchemy column type string."""
        internal_type = col.type.lower()

        if internal_type in ("str", "varchar", "text"):
            return f"String({col.max_length})" if col.max_length else "Text"

        if internal_type == "enum":
            # TODO: replace comment-based encoding with enum_values field on ColumnModel
            values = col.comment.replace("ENUM:", "").split(",") if col.comment else []
            return f"Enum({', '.join(f'{v!r}' for v in values)})" if values else "String(255)"

        if internal_type == "decimal":
            precision = getattr(col, "precision", 10) or 10
            scale = getattr(col, "scale", 2) or 2
            return f"Numeric(precision={precision}, scale={scale})"

        mapping = {
            "int": "Integer",
            "float": "Float",
            "bool": "Boolean",
            "date": "Date",
            "datetime": "DateTime",
            "json": "JSON",
        }
        return mapping.get(internal_type, "String(255)")

    def _map_to_python(self, internal_type: str) -> str:
        """Map a normalized column type to its Python type annotation string."""
        mapping = {
            "int": "int",
            "str": "str",
            "varchar": "str",
            "text": "str",
            "float": "float",
            "decimal": "float",
            "bool": "bool",
            "date": "date",
            "datetime": "datetime",
            "json": "dict",
            "enum": "str",
        }
        return mapping.get(internal_type.lower(), "Any")

    def _to_snake_case(self, s: str) -> str:
        """Convert CamelCase or PascalCase to snake_case."""
        s = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', s)
        s = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s)
        return s.lower()

    def _to_pascal_case(self, s: str) -> str:
        """Convert snake_case to PascalCase."""
        return "".join(word.capitalize() for word in s.split("_"))

    def _parse_enum_values(self, comment: str) -> str:
        """Convert 'ENUM:Male,Female' to '"Male", "Female"' for use in Literal[]."""
        if not comment or not comment.startswith("ENUM:"):
            return ""
        values = comment.replace("ENUM:", "").split(",")
        return ", ".join(f'"{v.strip()}"' for v in values)