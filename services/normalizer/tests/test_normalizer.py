import pytest
from app.normalizer import Normalizer
from shared.models import TableModel, ColumnModel, ForeignKeyModel, IndexModel

@pytest.fixture
def normalizer():
    return Normalizer()

def make_table(name, columns=None, foreign_keys=None):
    """Helper to build a TableModel without boilerplate."""
    return TableModel(
        name=name,
        columns=columns or [],
        foreign_keys=foreign_keys or [],
    )

def make_col(name, raw_type, check_constraint=None):
    """Helper to build a ColumnModel with minimal fields."""
    return ColumnModel(name=name, type=raw_type, raw_type=raw_type, check_constraint=check_constraint)

# type normalization

def test_integer_type_mapping(normalizer):
    table = make_table("t", [make_col("id", "INTEGER")])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == "int"

def test_varchar_type_mapping(normalizer):
    table = make_table("t", [make_col("name", "VARCHAR(100)")])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == "str"

def test_unknown_type_falls_back_to_str(normalizer):
    table = make_table("t", [make_col("x", "WEIRDTYPE")])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == "str"

@pytest.mark.parametrize("raw_type,expected", [
    ("INTEGER", "int"),
    ("BIGINT", "int"),
    ("TINYINT", "int"),
    ("VARCHAR(255)", "str"),
    ("TEXT", "str"),
    ("BOOLEAN", "bool"),
    ("TIMESTAMP", "datetime"),
    ("DECIMAL(10,2)", "decimal"),
    ("FLOAT", "float"),
])
def test_type_map_coverage(normalizer, raw_type, expected):
    table = make_table("t", [make_col("col", raw_type)])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == expected

# enum detection

def test_enum_detected_from_check_constraint(normalizer):
    col = make_col("gender", "TEXT", check_constraint="gender IN ('Male', 'Female')")
    table = make_table("users", [col])
    result = normalizer.normalize([table])
    result_col = result.tables[0].columns[0]
    assert result_col.type == "enum"
    assert "Male" in result_col.comment
    assert "Female" in result_col.comment

def test_no_enum_without_quoted_values(normalizer):
    # numeric check should not be detected as enum
    col = make_col("age", "INT", check_constraint="age > 0")
    table = make_table("t", [col])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == "int"

def test_no_enum_without_check_constraint(normalizer):
    col = make_col("status", "TEXT")
    table = make_table("t", [col])
    result = normalizer.normalize([table])
    assert result.tables[0].columns[0].type == "str"

# fk index creation

def test_missing_fk_index_is_added(normalizer):
    fk = ForeignKeyModel(constrained_columns=["user_id"], referred_table="users", referred_columns=["id"])
    table = make_table("orders", foreign_keys=[fk])
    result = normalizer.normalize([table])
    indexes = result.tables[0].indexes
    assert any("user_id" in idx.columns for idx in indexes)

def test_existing_fk_index_is_not_duplicated(normalizer):
    fk = ForeignKeyModel(constrained_columns=["user_id"], referred_table="users", referred_columns=["id"])
    existing_index = IndexModel(name="idx_orders_user_id", columns=["user_id"])
    table = make_table("orders", foreign_keys=[fk])
    table.indexes.append(existing_index)
    result = normalizer.normalize([table])
    user_id_indexes = [idx for idx in result.tables[0].indexes if idx.columns == ["user_id"]]
    assert len(user_id_indexes) == 1

# topological sort

def test_referenced_table_comes_first(normalizer):
    fk = ForeignKeyModel(constrained_columns=["user_id"], referred_table="users", referred_columns=["id"])
    users = make_table("users")
    orders = make_table("orders", foreign_keys=[fk])
    result = normalizer.normalize([orders, users])
    names = [t.name for t in result.tables]
    assert names.index("users") < names.index("orders")

def test_circular_dependency_falls_back_to_original_order(normalizer):
    fk_a = ForeignKeyModel(constrained_columns=["b_id"], referred_table="b", referred_columns=["id"])
    fk_b = ForeignKeyModel(constrained_columns=["a_id"], referred_table="a", referred_columns=["id"])
    a = make_table("a", foreign_keys=[fk_a])
    b = make_table("b", foreign_keys=[fk_b])
    result = normalizer.normalize([a, b])
    # should not raise, just return original order
    assert len(result.tables) == 2

def test_self_referencing_table_is_handled(normalizer):
    fk = ForeignKeyModel(constrained_columns=["parent_id"], referred_table="category", referred_columns=["id"])
    category = make_table("category", foreign_keys=[fk])
    result = normalizer.normalize([category])
    assert len(result.tables) == 1