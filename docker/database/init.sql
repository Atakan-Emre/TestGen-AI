CREATE TABLE test_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,  -- BSC, NGI, OPT, NGV
    description TEXT
);

CREATE TABLE test_scenarios (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES test_categories(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    test_data JSONB,  -- JSON formatında test verisi
    expected_result VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_runs (
    id SERIAL PRIMARY KEY,
    scenario_id INTEGER REFERENCES test_scenarios(id),
    status VARCHAR(50),  -- SUCCESS, FAILED, PENDING
    result JSONB,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dosya yönetimi için yeni tablolar
CREATE TYPE file_type AS ENUM ('json', 'csv', 'txt');

CREATE TABLE csv_files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    content TEXT,
    size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE json_files (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    content JSONB,
    size BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE TABLE nlp_results (
    id SERIAL PRIMARY KEY,
    file_type file_type NOT NULL,
    file_id INTEGER,
    model_name VARCHAR(100),
    analysis_result JSONB,
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_csv_file FOREIGN KEY (file_id) REFERENCES csv_files(id),
    CONSTRAINT fk_json_file FOREIGN KEY (file_id) REFERENCES json_files(id),
    CONSTRAINT check_csv_type CHECK (file_type = 'csv' OR file_type = 'json')
);

CREATE TABLE file_versions (
    id SERIAL PRIMARY KEY,
    file_type file_type NOT NULL,
    file_id INTEGER,
    version INTEGER,
    content TEXT,
    json_content JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    CONSTRAINT fk_csv_file_version FOREIGN KEY (file_id) REFERENCES csv_files(id),
    CONSTRAINT fk_json_file_version FOREIGN KEY (file_id) REFERENCES json_files(id),
    CONSTRAINT check_file_type CHECK (file_type = 'csv' OR file_type = 'json')
);

-- Test kategorilerini ekle
INSERT INTO test_categories (name, description) VALUES 
('BSC', 'Basic Scenario Tests'),
('NGI', 'Negative/Invalid Tests'),
('OPT', 'Optional Field Tests'),
('NGV', 'Negative/Unique Tests');
