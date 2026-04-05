export interface ApiResponse<T> {
  files?: T;
  message?: string;
  error?: string;
}

// Category tipleri
export interface Category {
  id: number;
  name: string;
  description?: string;
  created_at: string;
  updated_at?: string;
}

export interface CategoryCreate {
  name: string;
  description?: string;
}

export interface CategoryUpdate {
  name?: string;
  description?: string;
}

export interface ScenarioFieldMetadata {
  field_name_tr: string;
  field_name_en: string;
  field_type?: string | null;
  raw_type?: string | null;
  required: boolean;
  optional: boolean;
  unique: boolean;
  max_len?: number | null;
  min_len?: number | null;
  pattern?: string | null;
  enum_values?: string[];
  semantic_tags?: string[];
  confidence?: number;
}

export interface ScenarioTypeDistribution {
  type: string;
  count: number;
}

export interface ScenarioMetadata {
  scenario_name: string;
  source_csv: string;
  generator_type: string;
  generated_at: string;
  field_count: number;
  required_count: number;
  optional_count: number;
  unique_count: number;
  average_confidence: number;
  semantic_tags: string[];
  type_distribution: ScenarioTypeDistribution[];
  fields?: ScenarioFieldMetadata[];
}

export interface ScenarioGenerationLogEntry {
  timestamp: string;
  level: string;
  message: string;
}

export interface ScenarioGenerationJobResult {
  message: string;
  scenarios: string[];
  scenario_file?: string | null;
  summary?: ScenarioMetadata | null;
}

export interface ScenarioGenerationJob {
  job_id: string;
  request: Record<string, unknown>;
  status: 'queued' | 'running' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  logs: ScenarioGenerationLogEntry[];
  result?: ScenarioGenerationJobResult | null;
  error?: string | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  updated_at: string;
}

// Scenario tipleri
export interface Scenario {
  id: number | string;
  name: string;
  full_name?: string;
  file_path?: string;
  csv_file_id?: number | null;
  created_at?: string;
  updated_at?: string | null;
  description?: string;
  content?: string;
  filename?: string;
  date?: string;
  size?: number;
  metadata?: ScenarioMetadata | null;
}

export interface ScenarioCreate {
  name: string;
  description?: string;
  csv_file_id?: number;
}

export interface ScenarioUpdate {
  name?: string;
  description?: string;
} 
