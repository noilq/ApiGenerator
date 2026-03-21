from shared.models import TableModel, ColumnModel, IndexModel
from app.models import NormalizerResponse
from typing import List
import re

class Normalizer:
    TYPE_MAP = {
        "integer": "int",
        "int": "int",
        "tinyint": "int",
        "smallint": "int",
        "bigint": "int",
        "varchar": "str",
        "text": "str",
        "string": "str",
        "char": "str",
        "boolean": "bool",
        "bool": "bool",
        "date": "date",
        "datetime": "datetime",
        "timestamp": "datetime",
        "float": "float",
        "real": "float",
        "double": "float",
        "decimal": "decimal",
        "numeric": "decimal"
    }

    def normalize(self, tables: List[TableModel]) -> NormalizerResponse:
        """Normalize column types, ensure FK indexes, and return tables in dependency order."""
        for table in tables:
            self._normalize_columns(table)
            self._ensure_indexes_for_fk(table)
        
        sorted_tables = self._topological_sort(tables)

        return NormalizerResponse(tables = sorted_tables)

    def _normalize_columns(self, table: TableModel):
        """Map raw db types to normalized types and detect ENUM columns from check constraints."""
        for col in table.columns:
            raw = col.raw_type.lower()
            
            # varchar(255) -> varchar
            base_type = re.sub(r'\(.*?\)', '', raw).strip()
            col.type = self.TYPE_MAP.get(base_type, "str")

            if col.check_constraint:
                self._detect_enum(col)
                
    def _detect_enum(self, col: ColumnModel):
        """
        Detect ENUM pattern from CHECK constraints and annotate the column.
        
        TODO: replace comment-based encoding with dedicated enum_values field on ColumnModel.
        """
        enum_values = re.findall(r"['\"](.*?)['\"]", col.check_constraint)
        if enum_values:
            col.type = "enum"
            col.comment = f"ENUM:{','.join(enum_values)}"

    def _ensure_indexes_for_fk(self, table: TableModel):
        """Add a btree index for any FK columns that are not already indexed."""
        existing_indexed_cols = {tuple(idx.columns) for idx in table.indexes}
        
        for fk in table.foreign_keys:
            cols_tuple = tuple(fk.constrained_columns)
            if cols_tuple not in existing_indexed_cols:
                index_name = f"idx_{table.name}_{'_'.join(fk.constrained_columns)}"
                table.indexes.append(IndexModel(
                    name = index_name,
                    columns = fk.constrained_columns,
                    unique = False,
                    method = "btree"
                ))

    def _topological_sort(self, tables: List[TableModel]) -> List[TableModel]:
        """
        Sort tables so that referenced tables come before the tables that reference them.

        Uses Kahn's algorithm. Falls back to original order if circular dependency is detected.
        """
        adj = {t.name: [] for t in tables}
        in_degree = {t.name: 0 for t in tables}
        table_map = {t.name: t for t in tables}

        for table in tables:
            for fk in table.foreign_keys:
                parent = fk.referred_table
                if parent in adj and parent != table.name:
                    adj[parent].append(table.name)
                    in_degree[table.name] += 1

        queue = [name for name, degree in in_degree.items() if degree == 0]
        sorted_list = []

        while queue:
            u = queue.pop(0)
            sorted_list.append(table_map[u])

            for v in adj[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(sorted_list) < len(tables):
            # circular dependency
            return tables
            
        return sorted_list