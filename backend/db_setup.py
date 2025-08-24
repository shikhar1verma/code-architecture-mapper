#!/usr/bin/env python3
"""
Simple database setup script for Code Architecture Mapper

This script handles database initialization using SQL migration files.
"""

import os
import sys
from pathlib import Path
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add backend to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from backend.database.connection import engine
from sqlalchemy import text

def get_db_config():
    """Extract database configuration from environment"""
    database_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/repo_architect"
    )
    
    # Parse the URL
    # Format: postgresql://user:password@host:port/database
    url_parts = database_url.replace("postgresql://", "").split("/")
    db_name = url_parts[1] if len(url_parts) > 1 else "repo_architect"
    
    user_host = url_parts[0].split("@")
    host_port = user_host[1] if len(user_host) > 1 else "localhost:5432"
    user_pass = user_host[0].split(":")
    
    user = user_pass[0] if len(user_pass) > 0 else "postgres"
    password = user_pass[1] if len(user_pass) > 1 else "postgres"
    
    host_port_split = host_port.split(":")
    host = host_port_split[0]
    port = int(host_port_split[1]) if len(host_port_split) > 1 else 5432
    
    return {
        'host': host,
        'port': port,
        'user': user,
        'password': password,
        'database': db_name
    }

def create_database_if_not_exists():
    """Create database if it doesn't exist"""
    config = get_db_config()
    
    # Connect to PostgreSQL server (not to specific database)
    try:
        conn = psycopg2.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres'  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (config['database'],))
        exists = cursor.fetchone()
        
        if not exists:
            print(f"🔄 Creating database '{config['database']}'...")
            cursor.execute(f'CREATE DATABASE "{config["database"]}"')
            print(f"✅ Database '{config['database']}' created successfully!")
        else:
            print(f"✅ Database '{config['database']}' already exists")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"❌ Error creating database: {e}")
        return False
    
    return True

def run_sql_file(sql_file_path):
    """Execute SQL file against the database"""
    if not os.path.exists(sql_file_path):
        print(f"❌ SQL file not found: {sql_file_path}")
        return False
    
    try:
        # Use SQLAlchemy engine to execute the SQL
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        with engine.connect() as connection:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement:  # Skip empty statements
                    connection.execute(text(statement))
            
            connection.commit()
        
        print(f"✅ Successfully executed: {sql_file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error executing SQL file: {e}")
        return False

def setup_database():
    """Complete database setup"""
    print("🚀 Setting up Code Architecture Mapper database...")
    
    # Create database if it doesn't exist
    if not create_database_if_not_exists():
        return False
    
    # Run initial migration (now includes intelligent diagrams)
    migrations_dir = backend_dir / "migrations"
    initial_schema = migrations_dir / "001_initial_schema.sql"
    
    if not run_sql_file(initial_schema):
        return False
    
    print("✅ Database setup completed successfully!")
    print("💡 You can now start the FastAPI application")
    print("🎯 Intelligent dependency diagrams are now supported!")
    return True

def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "init":
            setup_database()
        elif command == "create-db":
            create_database_if_not_exists()
        elif command == "run-migration":
            if len(sys.argv) < 3:
                print("❌ Usage: python db_setup.py run-migration <migration_file>")
                sys.exit(1)
            migration_file = backend_dir / "migrations" / sys.argv[2]
            run_sql_file(migration_file)
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands:")
            print("  init          - Complete database setup")
            print("  create-db     - Create database only")
            print("  run-migration <file> - Run specific migration file")
    else:
        # Default action
        setup_database()

if __name__ == "__main__":
    main() 