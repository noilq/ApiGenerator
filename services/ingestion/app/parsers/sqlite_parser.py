import sqlglot
from sqlglot import exp
from app.parsers.base import BaseParser
from shared.models import TableModel, ColumnModel, IndexModel, ForeignKeyModel  # TODO: rapse CREATE INDEX
from typing import List

class SQLiteParser(BaseParser):
    def __init__(self):
        self.dialect = "sqlite"

    def parse(self, raw_sql: str) -> List[TableModel]:
        """Parse raw SQL DDL and return list of TableModel objects."""
        tables = []

        expressions = sqlglot.parse(raw_sql, read=self.dialect)
        
        """
        return[
            self._parse_table(expr)
            for expr in expressions
            if isInstance(expr, exp.Create) and expr.args.get("kind") == "CREATE TABLE"
        ]
        """

        for expression in expressions:
            if isinstance(expression, exp.Create) and expression.args.get("kind") == "TABLE":
                tables.append(self._parse_table(expression))
            
        return tables
    
    def _parse_table(self, expression) -> TableModel:
        """Extract table name, columns, PK's, FK's from a CREATE TABLE expression."""
        table_def = expression.this
        table_info = table_def.this
        
        table_name = table_info.name
        db_identifier = table_info.args.get("db")
        schema_name = db_identifier.name if db_identifier else "public"

        columns = []
        foreign_keys = []
        pk_column_names = []

        for e in table_def.expressions:
            if isinstance(e, exp.ColumnDef):
                col, inline_fks, pk_names = self._parse_column(e, schema_name)
                columns.append(col)
                foreign_keys.extend(inline_fks)
                pk_column_names.extend(pk_names)
                
            elif isinstance(e, exp.ForeignKey):
                fk = self._parse_table_fk(e, schema_name)
                if fk:
                    foreign_keys.append(fk)

            elif isinstance(e, exp.PrimaryKey):
                # composite PK defined at table level e.g. PRIMARY KEY (col1, col2)
                pk_names = [c.name for c in e.expressions]
                pk_column_names.extend(pk_names)
                for col in columns:
                    if col.name in pk_names:
                        col.is_primary = True

        return TableModel(
            name=table_name,
            schema_name=schema_name,
            columns=columns,
            primary_key=list(dict.fromkeys(pk_column_names)),
            foreign_keys=foreign_keys,
        )

    def _parse_column(
        self, col_expr: exp.ColumnDef, schema_name: str) -> tuple[ColumnModel, List[ForeignKeyModel], List[str]]:
        """
        Parse a column definition, returning the column model, any inline FKs, and PK names.
        
        Returns:
            tuple
                - ColumnModel: object representing column
                - List[ForeignKeyModel]: list of inline FK's
                - List[str]: list of PK's
        """
        col_name = col_expr.name
        data_type = col_expr.kind

        raw_type = data_type.sql(dialect=self.dialect) if data_type else "TEXT"
        abstract_type = data_type.this.name.lower().strip() if data_type else "text"

        col_len = self._parse_column_length(data_type)
        is_pk, is_nullable, is_auto = False, True, False
        col_default, col_check = None, None
        inline_fks = []
        pk_names = []

        for constraint in col_expr.args.get("constraints", []):
            kind = constraint.kind

            if isinstance(kind, exp.PrimaryKeyColumnConstraint):
                is_pk = True
                pk_names.append(col_name)
            elif isinstance(kind, exp.NotNullColumnConstraint):
                is_nullable = False
            elif isinstance(kind, exp.AutoIncrementColumnConstraint):
                is_auto = True
            elif isinstance(kind, exp.DefaultColumnConstraint):
                col_default = kind.this.sql(dialect=self.dialect)
            elif isinstance(kind, exp.CheckColumnConstraint):
                col_check = kind.this.sql(dialect=self.dialect)
            elif isinstance(kind, exp.Reference):
                inline_fks.append(self._parse_inline_fk(col_name, kind, schema_name))

        column = ColumnModel(
            name=col_name,
            type=abstract_type,
            raw_type=raw_type,
            is_nullable=is_nullable,
            is_primary=is_pk,
            is_autoincrement=is_auto,
            default=col_default,
            check_constraint=col_check,
            max_length=col_len,
        )
        return column, inline_fks, pk_names

    def _parse_column_length(self, data_type) -> int | None:
        """Extract length e.g. VARCHAR(255) -> 255."""
        if data_type and data_type.expressions:
            param = data_type.expressions[0].this.name
            if param.isdigit():
                return int(param)
        return None

    def _parse_inline_fk(self, col_name: str, ref: exp.Reference, schema_name: str) -> ForeignKeyModel:
        """Parse an inline FK e.g. user_id INT REFERENCES users(id)."""
        ref_node = ref.find(exp.Table)
        ref_table_name = ref_node.name if ref_node else ref.this.name
        return ForeignKeyModel(
            constrained_columns=[col_name],
            referred_schema=schema_name,
            referred_table=ref_table_name,
            referred_columns=[col.name for col in ref.this.expressions],
            on_delete="NO ACTION",      # TODO: extract on delete
            on_update="NO ACTION",      # TODO: extract on update
        )

    def _parse_table_fk(self, fk_expr: exp.ForeignKey, schema_name: str) -> ForeignKeyModel | None:
        """Parse a table-level FK e.g. FOREIGN KEY (id) REFERENCES log(source_id)."""
        reference = fk_expr.args.get("reference")
        if not reference:
            return None
        return ForeignKeyModel(
            name=None,
            constrained_columns=[col.name for col in fk_expr.expressions],
            referred_schema=schema_name,
            referred_table=reference.this.this.name,
            referred_columns=[col.name for col in reference.this.expressions],
            on_delete="NO ACTION",      # TODO: extract on delete
            on_update="NO ACTION",      # TODO: extract on update
        )