#!/usr/bin/env python3
"""
Schema generator for Atlas migration.
This script generates a PostgreSQL schema from SQLAlchemy models.
"""

import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.schema import CreateTable, CreateIndex
from sqlalchemy.dialects import postgresql

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

# Import all models to ensure they're registered with the Base
from src.server.database.models.software import Base, Software


def generate_schema():
    """Generate PostgreSQL schema from SQLAlchemy models."""
    
    # Create a PostgreSQL engine for proper dialect compilation
    engine = create_engine("postgresql://", strategy='mock', executor=lambda sql, *_: None)
    
    # Get all tables from the metadata
    metadata = Base.metadata
    
    # Generate DDL statements
    ddl_statements = []
    
    # Create tables
    for table in metadata.sorted_tables:
        create_table_stmt = CreateTable(table)
        ddl = str(create_table_stmt.compile(
            engine, 
            compile_kwargs={"literal_binds": True}
        ))
        ddl_statements.append(ddl + ";")
    
    # Create indexes
    for table in metadata.sorted_tables:
        for index in table.indexes:
            create_index_stmt = CreateIndex(index)
            ddl = str(create_index_stmt.compile(
                engine,
                compile_kwargs={"literal_binds": True}
            ))
            ddl_statements.append(ddl + ";")
    
    # Output the schema
    schema_sql = "\n".join(ddl_statements)
    print(schema_sql)


if __name__ == "__main__":
    generate_schema()
