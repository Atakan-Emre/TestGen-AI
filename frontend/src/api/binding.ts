import { API_URL } from '../config';
import type {
  BindingFieldRule,
  BindingAutoResolveResult,
  BindingAutoResolveSummary,
  BindingValidationResult,
  BindingProfile,
  BindingProfileSummary,
  BindingProfilesApiResponse,
  BindingProfileApiResponse,
  BindingSuggestionData,
  BindingSuggestionApiResponse,
  BindingGeneratorKey,
} from '../types/binding';

const mapBackendActionToUi = (action: string) => {
  switch (action) {
    case 'bind':
    case 'variable':
      return 'use_variable';
    case 'preserve':
    case 'keep_template':
    case 'do_not_touch':
      return 'keep_template';
    case 'force_null':
      return 'force_null';
    case 'ignore':
      return 'do_not_touch';
    case 'generate':
    default:
      return 'generate_dynamic';
  }
};

const mapUiActionToBackend = (action: string) => {
  switch (action) {
    case 'use_variable':
      return 'bind';
    case 'keep_template':
      return 'keep_template';
    case 'force_null':
      return 'force_null';
    case 'do_not_touch':
      return 'ignore';
    case 'generate_dynamic':
    default:
      return 'generate';
  }
};

const mapSuggestionField = (field: any): BindingFieldRule => {
  const approved =
    typeof field.approved === 'boolean'
      ? field.approved
      : field.status === 'matched' || field.status === 'template';
  return {
    json_path: field.json_path,
    schema_type: field.schema_type,
    suggested_variable_key: field.suggested_variable_key ?? null,
    variable_key: field.variable_key ?? null,
    confidence: Number(field.confidence ?? 0),
    status: field.status ?? (approved ? 'matched' : 'ignored'),
    action: mapBackendActionToUi(field.action),
    approved,
    locked: Boolean(field.locked),
    generator_scope: Array.isArray(field.generators)
      ? (field.generators.map((value: string) => value.toLowerCase()) as BindingGeneratorKey[])
      : ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: field.template_value_preview ?? null,
    variable_value_preview: field.variable_value_preview ?? null,
  };
};

const mapSuggestionData = (data: any): BindingSuggestionData => ({
  json_file_id: data?.json_file_id ?? null,
  variables_profile: data?.variables_profile ?? null,
  total_fields: Number(data?.total_fields ?? 0),
  matched_fields: Number(data?.matched_fields ?? 0),
  unmatched_fields: Number(data?.unmatched_fields ?? 0),
  fields: Array.isArray(data?.fields) ? data.fields.map(mapSuggestionField) : [],
  generated_at: data?.generated_at,
});

const mapAutoResolveSummary = (summary: any): BindingAutoResolveSummary => ({
  total_fields: Number(summary?.total_fields ?? 0),
  matched_fields: Number(summary?.matched_fields ?? 0),
  suggested_fields: Number(summary?.suggested_fields ?? 0),
  generated_fields: Number(summary?.generated_fields ?? 0),
  template_fields: Number(summary?.template_fields ?? 0),
  bound_fields: Number(summary?.bound_fields ?? 0),
  approved_fields: Number(summary?.approved_fields ?? 0),
  match_ratio: Number(summary?.match_ratio ?? 0),
  average_confidence: Number(summary?.average_confidence ?? 0),
  min_confidence: Number(summary?.min_confidence ?? 0),
  review_recommended: Boolean(summary?.review_recommended),
  review_reasons: Array.isArray(summary?.review_reasons) ? summary.review_reasons : [],
});

const mapProfile = (profile: any): BindingProfile => ({
  name: profile.name,
  source: {
    scenario_name: profile.description || null,
    scenario_id: null,
    json_file_id: profile.json_file_id ?? null,
    json_file_name: null,
    variable_profiles: profile.variables_profile ? [profile.variables_profile] : [],
  },
  rules: Array.isArray(profile.bindings)
    ? profile.bindings.map(mapSuggestionField)
    : [],
  created_at: profile.created_at || new Date().toISOString(),
  updated_at: profile.updated_at || new Date().toISOString(),
});

export const bindingApi = {
  async suggestBindings(params: {
    json_file_id: number;
    variables_profile: string;
    generators?: BindingGeneratorKey[];
  }): Promise<BindingFieldRule[]> {
    const response = await fetch(`${API_URL}/bindings/suggest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        json_file_id: params.json_file_id,
        variables_profile: params.variables_profile,
        generators: params.generators,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data: BindingSuggestionApiResponse = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Binding önerileri alınamadı');
    }

    return mapSuggestionData(data.data).fields;
  },

  async autoResolve(params: {
    json_file_id: number;
    variables_profile: string;
    generators?: BindingGeneratorKey[];
    profile_name?: string;
    description?: string;
  }): Promise<BindingAutoResolveResult> {
    const response = await fetch(`${API_URL}/bindings/auto-resolve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Otomatik binding profili oluşturulamadı');
    }

    return {
      profile_name: data.data?.profile_name || '',
      review_recommended: Boolean(data.data?.review_recommended),
      summary: mapAutoResolveSummary(data.data?.summary),
      suggestion: mapSuggestionData(data.data?.suggestion || {}),
      saved_profile: data.data?.saved_profile ? mapProfile(data.data.saved_profile) : null,
    };
  },

  async validate(params: {
    scenario_id?: string;
    scenario_path?: string;
    json_file_id: number;
    variables_profile: string;
    generators?: BindingGeneratorKey[];
    binding_profile_name?: string;
    auto_resolve?: boolean;
    profile_name?: string;
    description?: string;
  }): Promise<BindingValidationResult> {
    const response = await fetch(`${API_URL}/bindings/validate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Binding doğrulama tamamlanamadı');
    }

    return data.data as BindingValidationResult;
  },

  async listProfiles(): Promise<BindingProfileSummary[]> {
    const response = await fetch(`${API_URL}/bindings/profiles`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data: BindingProfilesApiResponse = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Binding profilleri alınamadı');
    }

    return data.data.profiles || [];
  },

  async getProfile(name: string): Promise<BindingProfile> {
    const response = await fetch(`${API_URL}/bindings/profiles/${encodeURIComponent(name)}`);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data: BindingProfileApiResponse = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Binding profili yüklenemedi');
    }

    return mapProfile(data.data);
  },

  async saveProfile(profile: BindingProfile, description?: string): Promise<BindingProfile> {
    const response = await fetch(`${API_URL}/bindings/profiles/${encodeURIComponent(profile.name)}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        json_file_id: profile.source.json_file_id,
        variables_profile: profile.source.variable_profiles[0] || 'default',
        description: description || profile.source.json_file_name || profile.source.scenario_name || null,
        bindings: profile.rules.map((rule) => ({
          json_path: rule.json_path,
          schema_type: rule.schema_type,
          suggested_variable_key: rule.suggested_variable_key,
          variable_key: rule.variable_key,
          confidence: rule.confidence,
          status: rule.approved ? 'matched' : 'ignored',
          action: mapUiActionToBackend(rule.action),
          locked: rule.locked,
          generators: rule.generator_scope,
          approved: rule.approved,
        })),
      }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }

    const data: BindingProfileApiResponse = await response.json();
    if (!data.success) {
      throw new Error(data.message || 'Binding profili kaydedilemedi');
    }

    return mapProfile(data.data);
  },

  async deleteProfile(name: string): Promise<void> {
    const response = await fetch(`${API_URL}/bindings/profiles/${encodeURIComponent(name)}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
    }
  },
};
