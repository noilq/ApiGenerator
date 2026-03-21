import pytest
from app.parsers.sqlite_parser import SQLiteParser

@pytest.fixture
def parser():
    return SQLiteParser()

# basic parsing

def test_default_schema_is_public(parser):
    result = parser.parse("CREATE TABLE a (id INT);")
    assert result[0].schema_name == "public"

def test_explicit_schema_is_preserved(parser):
    sql = "CREATE TABLE main.users (id INT);"
    result = parser.parse(sql)
    assert result[0].schema_name == "main"

def test_non_create_statements_are_ignored(parser):
    sql = "SELECT * FROM x; DROP TABLE y; CREATE TABLE a (id INT);"
    result = parser.parse(sql)
    assert len(result) == 1
    assert result[0].name == "a"

def test_quoted_names_with_spaces(parser):
    sql = 'CREATE TABLE "Order Details" ("Line Item" INT);'
    result = parser.parse(sql)
    assert result[0].name == "Order Details"
    assert result[0].columns[0].name == "Line Item"

# column constraints

def test_primary_key_and_autoincrement(parser):
    sql = "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT);"
    col = parser.parse(sql)[0].columns[0]
    assert col.is_primary is True
    assert col.is_autoincrement is True

def test_not_null(parser):
    sql = "CREATE TABLE t (username TEXT NOT NULL);"
    col = parser.parse(sql)[0].columns[0]
    assert col.is_nullable is False

def test_default_value(parser):
    sql = "CREATE TABLE t (age INT DEFAULT 18);"
    col = parser.parse(sql)[0].columns[0]
    assert col.default == "18"

def test_check_constraint(parser):
    sql = "CREATE TABLE t (age INT CHECK (age >= 18));"
    col = parser.parse(sql)[0].columns[0]
    assert "age >= 18" in col.check_constraint

def test_varchar_max_length(parser):
    sql = "CREATE TABLE t (bio VARCHAR(255));"
    col = parser.parse(sql)[0].columns[0]
    assert col.max_length == 255

def test_multiple_constraints_on_same_column(parser):
    sql = "CREATE TABLE t (id INT PRIMARY KEY NOT NULL);"
    col = parser.parse(sql)[0].columns[0]
    assert col.is_primary is True
    assert col.is_nullable is False

def test_multiline_check_constraint(parser):
    sql = """
    CREATE TABLE products (
        price DECIMAL(10,2) CHECK (
            price > 0 AND
            status IN ('active', 'pending')
        )
    );
    """
    col = parser.parse(sql)[0].columns[0]
    assert "price > 0" in col.check_constraint

# primary keys

def test_composite_pk_at_table_level(parser):
    sql = """
    CREATE TABLE order_items (
        order_id INT,
        item_id INT,
        PRIMARY KEY (order_id, item_id)
    );
    """
    table = parser.parse(sql)[0]
    assert table.primary_key == ["order_id", "item_id"]
    for col in table.columns:
        assert col.is_primary is True

# foreign keys

def test_inline_fk(parser):
    sql = "CREATE TABLE orders (user_id INT REFERENCES users(id));"
    fk = parser.parse(sql)[0].foreign_keys[0]
    assert fk.constrained_columns == ["user_id"]
    assert fk.referred_table == "users"
    assert fk.referred_columns == ["id"]

def test_table_level_fk(parser):
    sql = """
    CREATE TABLE orders (
        id INT,
        FOREIGN KEY (id) REFERENCES log(source_id)
    );
    """
    fk = parser.parse(sql)[0].foreign_keys[0]
    assert fk.constrained_columns == ["id"]
    assert fk.referred_table == "log"
    assert fk.referred_columns == ["source_id"]

def test_inline_and_table_fk_together(parser):
    sql = """
    CREATE TABLE orders (
        id INT PRIMARY KEY,
        user_id INT REFERENCES users(id),
        FOREIGN KEY (id) REFERENCES log(source_id)
    );
    """
    fks = parser.parse(sql)[0].foreign_keys
    assert len(fks) == 2
    assert any(fk.constrained_columns == ["user_id"] for fk in fks)
    assert any(fk.constrained_columns == ["id"] for fk in fks)

def test_fk_without_explicit_referred_columns(parser):
    sql = "CREATE TABLE profile (user_id INT REFERENCES users);"
    fk = parser.parse(sql)[0].foreign_keys[0]
    assert fk.referred_table == "users"
    assert fk.referred_columns == []

# real world schemas

# source: https://github.com/dtaivpp/car_company_database/blob/master/Create_Tables.sql
CAR_COMPANY_SQL = """
    Create Table Customers(customer_id INTEGER PRIMARY KEY AUTOINCREMENT, first_name VARCHAR(50) NOT NULL, last_name VARCHAR(50) NOT NULL, gender STRING CHECK(gender = 'Male' or gender = 'Female'), household_income INTEGER, birthdate DATE NOT NULL, phone_number INTEGER NOT NULL, email VARCHAR(128));
    Create Table Car_Vins(vin INTEGER PRIMARY KEY AUTOINCREMENT, model_id INTEGER NOT NULL, option_set_id INTEGER NOT NULL, manufactured_date DATE NOT NULL, manufactured_plant_id INTEGER NOT NULL, FOREIGN KEY (model_id) REFERENCES Models(model_id), FOREIGN KEY (manufactured_plant_id) REFERENCES Manufacture_Plant(manufacture_plant_id), FOREIGN KEY (option_set_id) REFERENCES Car_Options(option_set_id));
    Create Table Car_Options(option_set_id INTEGER PRIMARY KEY AUTOINCREMENT, model_id INTEGER NULL, engine_id INTEGER NOT NULL, transmission_id INTEGER NOT NULL, chassis_id INTEGER NOT NULL, premium_sound_id INTEGER, color VARCHAR(30) NOT NULL, option_set_price INTEGER NOT NUll, FOREIGN KEY (model_id) REFERENCES Models(model_id), FOREIGN KEY (engine_id) REFERENCES Car_Parts(part_id), FOREIGN KEY (premium_sound_id) REFERENCES Car_Parts(part_id), FOREIGN KEY (transmission_id) REFERENCES Car_Parts(part_id), FOREIGN KEY (chassis_id) REFERENCES Car_Parts(part_id));
    Create Table Car_Parts(part_id INTEGER PRIMARY KEY AUTOINCREMENT, part_name VARCHAR(100) NOT NULL, manufacture_plant_id INTEGER NOT NULL, manufacture_start_date DATE NOT NUll, manufacture_end_date DATE, part_recall INTEGER DEFAULT 0 CHECK (part_recall = 0 or part_recall = 1), FOREIGN KEY (manufacture_plant_id) REFERENCES Manufacture_Plant(manufacture_plant_id));
    Create Table Brands(brand_id INTEGER PRIMARY KEY AUTOINCREMENT, brand_name VARCHAR(50) NOT NUll);
    Create Table Models(model_id INTEGER PRIMARY KEY AUTOINCREMENT, model_name VARCHAR(50) NOT NULL, model_base_price INTEGER NOT NULL, brand_id INTEGER NOT NULL, FOREIGN KEY (brand_id) REFERENCES Brands(brand_id));
    Create Table Customer_Ownership(customer_id INTEGER NOT NULL, vin INTEGER NOT NULL, purchase_date DATE NOT NULL, purchase_price INTEGER NOT NULL, warantee_expire_date DATE, dealer_id INTEGER NOT NULL, FOREIGN KEY (customer_id) REFERENCES Customers(customer_id), FOREIGN KEY (vin) REFERENCES Car_Vins(vin), FOREIGN KEY (dealer_id) REFERENCES Dealers(dealer_id), PRIMARY KEY (customer_id, vin));
    Create Table Manufacture_Plant(manufacture_plant_id INTEGER PRIMARY KEY AUTOINCREMENT, plant_name VARCHAR(50) NOT NULL, plant_type VARCHAR (7) CHECK (plant_type='Assembly' or plant_type='Parts'), plant_location VARCHAR(100), company_owned INTEGER CHECK(company_owned=0 or company_owned=1));
    Create Table Dealers(dealer_id INTEGER PRIMARY KEY AUTOINCREMENT, dealer_name VARCHAR(50) NOT NULL, dealer_address VARCHAR(100));
    Create Table Dealer_Brand(dealer_id INTEGER NOT NULL, brand_id INTEGER NOT NULL, FOREIGN KEY (dealer_id) REFERENCES Dealers(dealer_id), FOREIGN KEY (brand_id) REFERENCES Brands(brand_id), PRIMARY KEY (dealer_id, brand_id));
"""

def test_car_company_table_count(parser):
    result = parser.parse(CAR_COMPANY_SQL)
    assert len(result) == 10

def test_car_company_enum_check_constraint(parser):
    result = parser.parse(CAR_COMPANY_SQL)
    customers = next(t for t in result if t.name == "Customers")
    gender_col = next(c for c in customers.columns if c.name == "gender")
    assert "gender = 'Male' OR gender = 'Female'" in gender_col.check_constraint

def test_car_company_foreign_keys(parser):
    result = parser.parse(CAR_COMPANY_SQL)
    car_vins = next(t for t in result if t.name == "Car_Vins")
    assert len(car_vins.foreign_keys) == 3
    model_fk = next(fk for fk in car_vins.foreign_keys if fk.constrained_columns == ["model_id"])
    assert model_fk.referred_table == "Models"
    assert model_fk.referred_columns == ["model_id"]

def test_car_company_multiple_fks_to_same_table(parser):
    result = parser.parse(CAR_COMPANY_SQL)
    car_options = next(t for t in result if t.name == "Car_Options")
    car_parts_refs = [fk for fk in car_options.foreign_keys if fk.referred_table == "Car_Parts"]
    assert len(car_parts_refs) == 4

def test_car_company_composite_pk(parser):
    result = parser.parse(CAR_COMPANY_SQL)
    ownership = next(t for t in result if t.name == "Customer_Ownership")
    assert ownership.primary_key == ["customer_id", "vin"]
    assert next(c for c in ownership.columns if c.name == "customer_id").is_primary is True
    assert next(c for c in ownership.columns if c.name == "vin").is_primary is True