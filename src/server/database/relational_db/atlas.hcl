// Atlas configuration for SQLAlchemy models

data "external_schema" "sqlalchemy" {
    program = [
        "atlas-provider-sqlalchemy",
        "--path", "./models",
        "--dialect", "postgresql"
    ]
}

env "local" {
  src = data.external_schema.sqlalchemy.url
  # url = "postgresql://postgresUser:postgresPW@localhost:5455/tkf_relational_db?sslmode=disable"
  # Database connection using environment variables with defaults
  url = "postgresql://${getenv("POSTGRES_USER", "postgresUser")}:${getenv("POSTGRES_PASSWORD", "postgresPW")}@${getenv("POSTGRES_HOST", "localhost")}:${getenv("POSTGRES_PORT", "5455")}/${getenv("POSTGRES_DB", "tkf_relational_db")}?sslmode=disable"
  # Dev database for schema diffing
  dev = "docker://postgres/17/dev?search_path=public"
  migration {
    dir = "file://migrations"
  }
  format {
    migrate {
      diff = "{{ sql . \"  \" }}"
    }
  }
}

// Lint configuration
lint {
  // Enable destructive change detection
  destructive {
    error = true
  }
  
  // Data dependent changes
  data_depend {
    error = true
  }
  
  // Naming conventions
  naming {
    error   = true
    match   = "^[a-z]+(_[a-z]+)*$"
    message = "must be in snake_case"
  }
}
