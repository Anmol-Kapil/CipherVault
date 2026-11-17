from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import DATA_DIR

engine = create_engine(f"sqlite:///{(DATA_DIR / 'vault.db').as_posix()}", connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def initialize_database():
    Base.metadata.create_all(bind=engine)
    # Preserve files created by the previous local-only version.
    columns = {column['name'] for column in inspect(engine).get_columns('files')}
    with engine.begin() as connection:
        if 'storage_backend' not in columns:
            connection.execute(text("ALTER TABLE files ADD COLUMN storage_backend VARCHAR NOT NULL DEFAULT 'local'"))
        if 'storage_id' not in columns:
            connection.execute(text('ALTER TABLE files ADD COLUMN storage_id VARCHAR'))
