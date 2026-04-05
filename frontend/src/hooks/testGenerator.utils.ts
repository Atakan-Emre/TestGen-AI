import type { BindingProfilePayload } from '../types/binding';

export interface TestGeneratorRequest {
  test_type: string;
  scenario_path: string;
  test_name: string;
  json_file_id: number;
  selected_variables: string[];
  binding_profile?: string | BindingProfilePayload | null;
}

export interface GeneratorRunResult {
  type: string;
  success: boolean;
  message: string;
  test_result?: any;
  error?: string;
  variables_profile?: string;
  generated_cases: GeneratedCaseSummary[];
  generated_count: number;
}

export interface GeneratedCaseSummary {
  file_path?: string;
  file_name?: string;
  description?: string;
  scenario_type?: string;
  expected_result?: string;
  expected_message?: string;
}

export interface GeneratorDefinition {
  key: string;
  title: string;
  description: string;
  color: string;
  focus: string;
}

export interface GeneratorRunSummary {
  total: number;
  successCount: number;
  failureCount: number;
  successRate: number;
  successTypes: string[];
  failureTypes: string[];
}

export const GENERATOR_DEFINITIONS: GeneratorDefinition[] = [
  {
    key: 'bsc',
    title: 'Temel Testler (BSC)',
    description: 'Pozitif akışlar için temel validasyon senaryoları',
    color: 'blue',
    focus: 'anlamsal eşleşme + geçerli payload',
  },
  {
    key: 'ngi',
    title: 'Negatif Testler (NGI)',
    description: 'Zorunlu alan, format ve enum ihlalleri',
    color: 'red',
    focus: 'geçersiz giriş politikaları',
  },
  {
    key: 'ngv',
    title: 'Negatif Değer Testleri (NGV)',
    description: 'Tekil alan ve duplicate-value kontrolü',
    color: 'orange',
    focus: 'tekrar değer tespiti',
  },
  {
    key: 'opt',
    title: 'Opsiyonel Testler (OPT)',
    description: 'Opsiyonel alan kombinasyonları ve varyasyonlar',
    color: 'green',
    focus: 'kapsam kombinasyonları',
  },
];

const VARIABLE_AWARE_GENERATORS = new Set(['bsc', 'ngi', 'ngv', 'opt']);

export const generatorUsesVariables = (generatorType: string) =>
  VARIABLE_AWARE_GENERATORS.has(generatorType);

export const getGeneratorDefinition = (generatorType: string) =>
  GENERATOR_DEFINITIONS.find((definition) => definition.key === generatorType);

export const extractVariablesProfile = (selectedVariables: string[]) => {
  const selectedProfile = selectedVariables.find((value) =>
    value.startsWith('variables_file:')
  );

  if (!selectedProfile) {
    return undefined;
  }

  return selectedProfile.replace('variables_file:', '').replace(/\.[^.]+$/, '');
};

export const buildTestPayload = (
  generatorType: string,
  request: TestGeneratorRequest
) => {
  const variablesProfile = extractVariablesProfile(request.selected_variables);
  const bindingProfile = request.binding_profile || undefined;
  const serializedBindingProfile =
    typeof bindingProfile === 'string'
      ? bindingProfile
      : bindingProfile
        ? JSON.stringify(bindingProfile)
        : undefined;

  if (generatorType === 'bsc') {
    return {
      ...request,
      test_type: generatorType,
      ...(serializedBindingProfile ? { binding_profile: serializedBindingProfile } : {}),
    };
  }

  return {
    scenario_id: request.scenario_path,
    test_name: request.test_name,
    json_files: [request.json_file_id],
    ...((generatorType === 'ngi' || generatorType === 'ngv' || generatorType === 'opt') && variablesProfile
      ? { variables_profile: variablesProfile }
      : {}),
    ...(serializedBindingProfile ? { binding_profile: serializedBindingProfile } : {}),
  };
};

export const normalizeGeneratorResult = (
  generatorType: string,
  data: any,
  selectedVariables: string[]
): GeneratorRunResult => {
  const variablesProfile = extractVariablesProfile(selectedVariables);
  const rawResult =
    typeof data?.success === 'boolean' ? data?.test_result : data?.result;
  const generatedCases = (Array.isArray(rawResult) ? rawResult : rawResult ? [rawResult] : []).map(
    (item: any) => ({
      file_path: item?.file_path,
      file_name: item?.file_name || item?.file_path?.split('/').pop(),
      description: item?.description,
      scenario_type: item?.scenario_type,
      expected_result: item?.expected_result,
      expected_message: item?.expected_message,
    })
  );
  const normalized =
    typeof data?.success === 'boolean'
      ? data
      : {
          success: true,
          message: data?.message || 'Test başarıyla oluşturuldu',
          test_result: Array.isArray(data?.result) ? data.result[0] : data?.result,
        };

  return {
    type: generatorType,
    success: Boolean(normalized.success),
    message: normalized.message || 'İşlem tamamlandı',
    test_result: normalized.test_result,
    error: normalized.error,
    variables_profile: variablesProfile,
    generated_cases: generatedCases,
    generated_count: generatedCases.length,
  };
};

export const summarizeGeneratorRuns = (
  results: GeneratorRunResult[]
): GeneratorRunSummary => {
  const successTypes = results.filter((result) => result.success).map((result) => result.type);
  const failureTypes = results.filter((result) => !result.success).map((result) => result.type);
  const total = results.length;
  const successCount = successTypes.length;
  const failureCount = failureTypes.length;

  return {
    total,
    successCount,
    failureCount,
    successRate: total > 0 ? Math.round((successCount / total) * 100) : 0,
    successTypes,
    failureTypes,
  };
};
