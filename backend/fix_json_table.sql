-- JSON files tablosuna type kolonu ekle
ALTER TABLE json_files ADD COLUMN IF NOT EXISTS type VARCHAR DEFAULT 'default';
