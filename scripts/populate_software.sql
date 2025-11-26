-- Script to populate the software table with sample data
-- Run this script against your PostgreSQL database

-- TRUNCATE TABLE software;

-- Populate entries into the software table
-- poetry run psql postgresql://postgresUser:postgresPW@localhost:5455/tkf_relational_db -f scripts/populate_software.sql


-- Insert info-extraction software with random JSON config
INSERT INTO software (type, config, created_at, updated_at) 
VALUES (
    'KnowledgeAdapterTemplates',
    '{
        "extraction": {
            "entities": ["PERSON", "ORG", "GPE", "DATE"],
            "confidence_threshold": 0.85,
            "use_crf": true,
            "preprocessing": {
                "lowercase": false,
                "remove_punctuation": true,
                "tokenizer": "wordpiece"
            }
        }
    }'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

INSERT INTO software (type, config, created_at, updated_at)
VALUES (
    'KnowledgeAdapterTemplates',
    '{
  "resourceSpans": [
    {
      "resource": {
        "attributes": [
          {
            "key": "service.name",
            "value": {
              "stringValue": "my-service"
            }
          },
          {
            "key": "host.name",
            "value": {
              "stringValue": "my-host"
            }
          }
        ]
      },
      "scopeSpans": [
        {
          "scope": {
            "name": "my-library",
            "version": "1.0.0"
          },
          "spans": [
            {
              "traceId": "0123456789abcdef0123456789abcdef",
              "spanId": "abcdef0123456789",
              "parentSpanId": "0123456789abcdef",
              "name": "parent-operation",
              "kind": "SPAN_KIND_SERVER",
              "startTimeUnixNano": "1678886400000000000",
              "endTimeUnixNano": "1678886400000000500",
              "attributes": [
                {
                  "key": "http.method",
                  "value": {
                    "stringValue": "GET"
                  }
                },
                {
                  "key": "http.status_code",
                  "value": {
                    "intValue": "200"
                  }
                }
              ],
              "events": [
                {
                  "timeUnixNano": "1678886400000000100",
                  "name": "log",
                  "attributes": [
                    {
                      "key": "message",
                      "value": {
                        "stringValue": "Request received"
                      }
                    }
                  ]
                }
              ],
              "status": {
                "code": "STATUS_CODE_OK"
              }
            },
            {
              "traceId": "0123456789abcdef0123456789abcdef",
              "spanId": "fedcba9876543210",
              "parentSpanId": "abcdef0123456789",
              "name": "child-operation",
              "kind": "SPAN_KIND_CLIENT",
              "startTimeUnixNano": "1678886400000000200",
              "endTimeUnixNano": "1678886400000000400",
              "attributes": [
                {
                  "key": "db.statement",
                  "value": {
                    "stringValue": "SELECT * FROM users"
                  }
                }
              ],
              "status": {
                "code": "STATUS_CODE_OK"
              }
            }
          ]
        }
      ]
    }
  ]
}'::jsonb,
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);
