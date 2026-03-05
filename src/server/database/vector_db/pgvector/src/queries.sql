 https://github.com/pgvector/pgvector/tree/v0.8.1?tab=readme-ov-file

CREATE TABLE document_embeddings (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
    created_by VARCHAR DEFAULT current_user,
    updated_by VARCHAR DEFAULT current_user,
    wksp_uuid UUID NOT NULL,
    mas_uuid UUID NOT NULL,
    document_txt VARCHAR NOT NULL,
    embedding_vector VECTOR(3) NOT NULL
);
CREATE INDEX document_vector_embedding_idx ON document_embeddings USING hnsw (embedding_vector vector_l2_ops);

INSERT INTO document_embeddings (id, wksp_uuid, mas_uuid, document_txt, embedding_vector)
VALUES
    ('7cf39bb8-e1a6-42c6-a157-678c1a37d244', '6cf39bb8-e1a6-42c6-a157-678c1a37d244', '9cf39bb8-e1a6-42c6-a157-678c1a37d244', 'abcde', '[1,2,3]'),
    ('7cf39bb8-e1a6-42c6-a157-678c1a37d245', '6cf39bb8-e1a6-42c6-a157-678c1a37d244', '9cf39bb8-e1a6-42c6-a157-678c1a37d244', 'pqrst', '[4,5,6]')
ON CONFLICT (id) DO UPDATE SET
    mas_uuid = EXCLUDED.mas_uuid,
    document_txt = EXCLUDED.document_txt,
    embedding_vector = EXCLUDED.embedding_vector;

SELECT document_txt, embedding_vector, embedding_vector <-> '[3,1,2]' AS distance from document_embeddings ORDER BY embedding_vector <-> '[3,1,2]';