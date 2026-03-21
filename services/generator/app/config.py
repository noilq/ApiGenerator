DB_CONFIG = {
    "sqlite": {
        "image": None,
        "port": None,
        "driver": None,
        "url_example": "sqlite:///./{{ project_name }}.db",
        "healthcheck": None,
        "supports_schemas": False,
        "supports_enums": False,
        "data_path": None,
    },
    "postgres": {
        "image": "postgres:16-alpine",
        "port": "5432:5432",
        "driver": "psycopg2-binary",
        "url_example": "postgresql://user:password@db:5432/{{ project_name }}",
        "healthcheck": "pg_isready",
        "supports_schemas": True,
        "supports_enums": True,
        "data_path": "/var/lib/postgresql/data",
    },
    "mysql": {
        "image": "mysql:8",
        "port": "3306:3306",
        "driver": "pymysql",
        "url_example": "mysql+pymysql://user:password@db:3306/{{ project_name }}",
        "healthcheck": "mysqladmin ping",
        "supports_schemas": False,
        "supports_enums": False,
        "data_path": "/var/lib/mysql",
    },
}

def get_db_config(db_type: str):
    """
    return[image, port, driver, url_example, healthcheck, supports_schemas, supports_enums]
    """
    return DB_CONFIG.get(db_type, DB_CONFIG["sqlite"])