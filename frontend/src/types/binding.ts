export type BindingAction =
  | 'use_variable'
  | 'generate_dynamic'
  | 'keep_template'
  | 'do_not_touch'
  | 'force_null';

export type BindingGeneratorKey = 'bsc' | 'ngi' | 'ngv' | 'opt';

export interface BindingFieldRule {
  json_path: string;
  schema_type: string;
  suggested_variable_key: string | null;
  variable_key: string | null;
  confidence: number;
  status: 'matched' | 'suggested' | 'generated' | 'template' | 'ignored' | 'unmapped';
  action: BindingAction;
  approved: boolean;
  locked: boolean;
  generator_scope: BindingGeneratorKey[];
  template_value_preview?: string | null;
  variable_value_preview?: string | null;
}

export interface BindingProfileSource {
  scenario_name?: string | null;
  scenario_id?: number | string | null;
  json_file_id?: number | null;
  json_file_name?: string | null;
  variable_profiles: string[];
}

export interface BindingProfile {
  name: string;
  source: BindingProfileSource;
  rules: BindingFieldRule[];
  created_at: string;
  updated_at: string;
}

export interface BindingProfilePayload extends BindingProfile {
  json_file_id?: number | null;
  variables_profile?: string | null;
  description?: string | null;
  bindings?: Array<Record<string, unknown>>;
}

export interface BindingSuggestionInput {
  jsonContent: unknown;
  variablesMap: Record<string, string>;
  selectedGenerators: BindingGeneratorKey[];
  source: BindingProfileSource;
}

export interface BindingFieldEntryResponse {
  json_path: string;
  schema_type: string;
  suggested_variable_key?: string | null;
  variable_key?: string | null;
  confidence: number;
  status: string;
  action: string;
  locked: boolean;
  generators: string[];
}

export interface BindingSuggestionApiResponse {
  success: boolean;
  message: string;
  data: {
    json_file_id?: number | null;
    variables_profile?: string | null;
    total_fields: number;
    matched_fields: number;
    unmatched_fields: number;
    fields: BindingFieldEntryResponse[];
  generated_at?: string;
  };
}

export interface BindingAutoResolveSummary {
  total_fields: number;
  matched_fields: number;
  suggested_fields: number;
  generated_fields: number;
  template_fields: number;
  bound_fields: number;
  approved_fields: number;
  match_ratio: number;
  average_confidence: number;
  min_confidence: number;
  review_recommended: boolean;
  review_reasons: string[];
}

export interface BindingSuggestionData {
  json_file_id?: number | null;
  variables_profile?: string | null;
  total_fields: number;
  matched_fields: number;
  unmatched_fields: number;
  fields: BindingFieldRule[];
  generated_at?: string;
}

export interface BindingAutoResolveResult {
  profile_name: string;
  review_recommended: boolean;
  summary: BindingAutoResolveSummary;
  suggestion: BindingSuggestionData;
  saved_profile?: BindingProfile | null;
}

export interface BindingValidationGeneratorResult {
  generator: string;
  success: boolean;
  error?: string;
  result_count?: number;
  output_files?: string[];
  message?: string;
  duration_ms?: number;
}

export interface BindingValidationResult {
  scenario_id?: string | null;
  scenario_path: string;
  json_file_id?: number | null;
  variables_profile: string;
  binding_profile_name: string;
  binding_summary: BindingAutoResolveSummary | Record<string, unknown>;
  auto_binding?: BindingAutoResolveResult | null;
  validation_name: string;
  validated_at: string;
  generator_results: Record<string, BindingValidationGeneratorResult>;
  overall_success: boolean;
  report_path: string;
}

export interface BindingProfileSummary {
  name: string;
  json_file_id?: number | null;
  variables_profile?: string | null;
  description?: string | null;
  binding_count: number;
  size_bytes?: number;
  updated_at?: string | null;
}

export interface BindingProfilesApiResponse {
  success: boolean;
  message: string;
  data: {
    profiles: BindingProfileSummary[];
  };
}

export interface BindingProfileApiResponse {
  success: boolean;
  message: string;
  data: Record<string, unknown>;
}
