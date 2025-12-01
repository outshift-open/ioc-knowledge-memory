#!/usr/bin/env python3
"""
Atlas migration management script for easy database operations.
Assumes atlas is installed at /usr/local/bin/atlasgo
"""

import os
import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent.parent.parent
relational_db_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        if cwd is None:
            cwd = relational_db_root

        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True, cwd=cwd)
        print(f"✅ {description} completed successfully!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed!")
        print(f"Error: {e.stderr}")
        return False


def generate_migration(message, env="local"):
    """Generate a new migration with Atlas."""
    cmd = f"/usr/local/bin/atlasgo migrate diff --env {env} '{message}'"
    return run_command(cmd, f"Generating migration: {message}")


def apply_migrations(env="local"):
    """Apply all pending migrations."""
    cmd = f"/usr/local/bin/atlasgo migrate apply --env {env}"
    return run_command(cmd, "Applying migrations")


def show_migration_status(env="local"):
    """Show migration status."""
    cmd = f"/usr/local/bin/atlasgo migrate status --env {env}"
    return run_command(cmd, "Showing migration status")


def validate_migrations(env="local"):
    """Validate migration files."""
    cmd = f"/usr/local/bin/atlasgo migrate validate --env {env}"
    return run_command(cmd, "Validating migrations")


def lint_schema(env="local"):
    """Lint the schema for issues."""
    cmd = f"/usr/local/bin/atlasgo schema inspect --env {env} --format '{{ json . }}'"
    return run_command(cmd, "Linting schema")


def test_schema_generation():
    """Test if schema generation works."""
    cmd = "python ../schema_generator.py"
    return run_command(cmd, "Testing schema generation")


def main():
    """Main CLI interface."""
    if len(sys.argv) < 2:
        print(
            """
🗄️  Atlas Migration Manager

Usage:
    python src/server/database/relational_db/scripts/atlas_migrate.py <command> [args]

Commands:
    generate <message> [env]    Generate new migration (default env: local)
    apply [env]                Apply all pending migrations (default env: local)
    status [env]               Show migration status (default env: local)
    validate [env]             Validate migration files (default env: local)
    lint [env]                 Lint schema for issues (default env: local)
    test-schema               Test schema generation from models
    
Examples:
    python src/server/database/relational_db/scripts/atlas_migrate.py generate "Add software table"
    python src/server/database/relational_db/scripts/atlas_migrate.py apply
    python src/server/database/relational_db/scripts/atlas_migrate.py status
    python src/server/database/relational_db/scripts/atlas_migrate.py generate "Update software model" dev
        """
        )
        return

    command = sys.argv[1]

    if command == "generate":
        if len(sys.argv) < 3:
            print("❌ Please provide a migration message")
            return
        message = sys.argv[2]
        env = sys.argv[3] if len(sys.argv) > 3 else "local"
        generate_migration(message, env)

    elif command == "apply":
        env = sys.argv[2] if len(sys.argv) > 2 else "local"
        apply_migrations(env)

    elif command == "status":
        env = sys.argv[2] if len(sys.argv) > 2 else "local"
        show_migration_status(env)

    elif command == "validate":
        env = sys.argv[2] if len(sys.argv) > 2 else "local"
        validate_migrations(env)

    elif command == "lint":
        env = sys.argv[2] if len(sys.argv) > 2 else "local"
        lint_schema(env)

    elif command == "test-schema":
        test_schema_generation()

    else:
        print(f"❌ Unknown command: {command}")


if __name__ == "__main__":
    main()
