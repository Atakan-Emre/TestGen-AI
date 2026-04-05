import type {
  BindingAction,
  BindingFieldRule,
  BindingGeneratorKey,
  BindingProfile,
  BindingProfilePayload,
  BindingProfileSource,
  BindingSuggestionInput,
} from '../types/binding';

const BINDING_STORAGE_KEY = 'testgen-ai.binding-profiles.v1';
const LEGACY_BINDING_STORAGE_KEY = 'test-scenario.binding-profiles.v1';
const GENERATOR_SCOPE_DEFAULT: BindingGeneratorKey[] = ['bsc', 'ngi', 'ngv', 'opt'];
const GENERIC_MATCH_TOKENS = new Set([
  'id',
  'code',
  'number',
  'nr',
  'no',
  'name',
  'description',
  'date',
  'time',
  'type',
  'status',
  'value',
  'values',
]);

const tokenize = (value: string) =>
  value
    .toLowerCase()
    .replace(/\[(\d+)\]/g, '.$1')
    .split(/[^a-z0-9]+/i)
    .filter(Boolean);

const normalizePath = (value: string) =>
  value
    .toLowerCase()
    .replace(/\[(\d+)\]/g, '.$1')
    .replace(/[^a-z0-9.]+/g, '');

const stringifyPreview = (value: unknown) => {
  if (value === null || value === undefined) {
    return null;
  }

  if (typeof value === 'string') {
    return value.length > 120 ? `${value.slice(0, 117)}...` : value;
  }

  if (typeof value === 'number' || typeof value === 'boolean') {
    return String(value);
  }

  try {
    const serialized = JSON.stringify(value);
    return serialized.length > 120 ? `${serialized.slice(0, 117)}...` : serialized;
  } catch {
    return null;
  }
};

const inferSchemaType = (value: unknown, path: string): string => {
  const pathLower = path.toLowerCase();

  if (Array.isArray(value)) {
    return 'array';
  }

  if (value === null || value === undefined) {
    if (pathLower.includes('date') || pathLower.includes('time')) return 'date';
    if (pathLower.endsWith('.id') || pathLower.endsWith('id')) return 'id';
    if (pathLower.includes('currency')) return 'currency';
    if (pathLower.includes('amount') || pathLower.includes('quantity') || pathLower.includes('rate')) return 'numeric';
    return 'unknown';
  }

  if (typeof value === 'boolean') return 'boolean';
  if (typeof value === 'number') return 'numeric';
  if (typeof value === 'string') {
    if (pathLower.includes('date') || pathLower.includes('time')) return 'date';
    if (pathLower.endsWith('.id') || pathLower.endsWith('id')) return 'id';
    if (pathLower.includes('currency')) return 'currency';
    if (pathLower.includes('amount') || pathLower.includes('quantity') || pathLower.includes('rate')) return 'numeric';
    if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value)) return 'uuid';
    return 'string';
  }

  if (typeof value === 'object') return 'object';
  return 'unknown';
};

const flattenJsonLeaves = (
  value: unknown,
  path = '',
  leaves: Array<{ path: string; value: unknown; schema_type: string }> = []
) => {
  if (Array.isArray(value)) {
    if (value.length === 0) {
      leaves.push({ path, value: [], schema_type: 'array' });
      return leaves;
    }

    flattenJsonLeaves(value[0], `${path}[0]`, leaves);
    return leaves;
  }

  if (value && typeof value === 'object') {
    Object.entries(value as Record<string, unknown>).forEach(([key, nestedValue]) => {
      const nextPath = path ? `${path}.${key}` : key;
      if (nestedValue && typeof nestedValue === 'object' && !Array.isArray(nestedValue)) {
        flattenJsonLeaves(nestedValue, nextPath, leaves);
      } else if (Array.isArray(nestedValue)) {
        flattenJsonLeaves(nestedValue, nextPath, leaves);
      } else {
        leaves.push({
          path: nextPath,
          value: nestedValue,
          schema_type: inferSchemaType(nestedValue, nextPath),
        });
      }
    });
  }

  return leaves;
};

const looksLikeDateValue = (value: string) =>
  /^\d{4}-\d{2}-\d{2}/.test(value) || /\d{2}\.\d{2}\.\d{4}/.test(value);

const inferVariableType = (variableKey: string, variableValue: string) => {
  const keyNormalized = normalizePath(variableKey);
  if (variableValue === 'true' || variableValue === 'false') {
    return 'boolean';
  }
  if (looksLikeDateValue(variableValue) || keyNormalized.includes('date') || keyNormalized.includes('time')) {
    return 'date';
  }
  if (/^-?\d+(\.\d+)?$/.test(variableValue) &&
    ['amount', 'quantity', 'rate', 'ratio', 'count', 'total', 'exchange'].some((token) =>
      keyNormalized.includes(token)
    )) {
    return 'numeric';
  }
  if (/^[0-9a-f-]{16,}$/i.test(variableValue) || keyNormalized.endsWith('.id') || keyNormalized.endsWith('id')) {
    return 'id';
  }
  if (keyNormalized.includes('type') || keyNormalized.includes('class')) {
    return 'string';
  }
  return 'string';
};

const areTypesCompatible = (schemaType: string, variableType: string) => {
  if (schemaType === variableType) {
    return true;
  }
  if (schemaType === 'string' && variableType === 'string') {
    return true;
  }
  if (schemaType === 'uuid' && variableType === 'id') {
    return true;
  }
  return false;
};

const scoreVariableMatch = (
  jsonPath: string,
  schemaType: string,
  variableKey: string,
  variableValue: string
) => {
  const pathNormalized = normalizePath(jsonPath);
  const keyNormalized = normalizePath(variableKey);
  const pathTokens = tokenize(jsonPath);
  const keyTokens = tokenize(variableKey);
  const specificPathTokens = pathTokens.filter((token) => !GENERIC_MATCH_TOKENS.has(token));
  const specificKeyTokens = keyTokens.filter((token) => !GENERIC_MATCH_TOKENS.has(token));
  const specificOverlap = specificKeyTokens.filter((token) => specificPathTokens.includes(token));
  const variableType = inferVariableType(variableKey, variableValue);

  if (pathNormalized === keyNormalized) {
    return 1;
  }

  if (!areTypesCompatible(schemaType, variableType)) {
    return 0;
  }

  const pathLeaf = tokenize(jsonPath.split('.').slice(-1)[0] || '').filter((token) => !GENERIC_MATCH_TOKENS.has(token));
  const keyLeaf = tokenize(variableKey.split('.').slice(-1)[0] || '').filter((token) => !GENERIC_MATCH_TOKENS.has(token));
  const pathContext = specificPathTokens.slice(0, Math.max(0, specificPathTokens.length - pathLeaf.length));
  const keyContext = specificKeyTokens.slice(0, Math.max(0, specificKeyTokens.length - keyLeaf.length));

  if (
    pathLeaf.length > 0 &&
    keyLeaf.length > 0 &&
    pathLeaf.join('.') === keyLeaf.join('.') &&
    pathContext.some((token) => keyContext.includes(token))
  ) {
    return 0.95;
  }

  if (specificOverlap.length === 0) {
    return 0;
  }

  const union = new Set([...specificPathTokens, ...specificKeyTokens]).size || 1;
  const baseScore = Math.min(0.88, 0.58 + 0.28 * (specificOverlap.length / union));

  let bonus = 0;
  if (schemaType === 'id' || schemaType === 'uuid') {
    if (/^[0-9a-f-]{16,}$/i.test(variableValue)) bonus += 0.08;
  }
  if (schemaType === 'date' && looksLikeDateValue(variableValue)) {
    bonus += 0.08;
  }
  if (schemaType === 'numeric' && /^-?\d+(\.\d+)?$/.test(variableValue)) {
    bonus += 0.05;
  }

  return Math.min(0.9, baseScore + bonus);
};

const defaultActionFor = (schemaType: string, templateValue: unknown, hasVariable: boolean): BindingAction => {
  if (hasVariable) {
    return 'use_variable';
  }

  if (templateValue === null || templateValue === undefined) {
    return schemaType === 'object' || schemaType === 'array' ? 'do_not_touch' : 'generate_dynamic';
  }

  if (schemaType === 'object' || schemaType === 'array') {
    return 'do_not_touch';
  }

  return 'keep_template';
};

const defaultScopeFor = (action: BindingAction): BindingGeneratorKey[] => {
  if (action === 'do_not_touch') {
    return [];
  }

  return GENERATOR_SCOPE_DEFAULT;
};

const detectBestVariable = (
  jsonPath: string,
  schemaType: string,
  variablesMap: Record<string, string>
) => {
  let bestKey: string | null = null;
  let bestValue: string | null = null;
  let bestScore = 0;

  Object.entries(variablesMap).forEach(([key, value]) => {
    const score = scoreVariableMatch(jsonPath, schemaType, key, String(value));
    if (score > bestScore) {
      bestKey = key;
      bestValue = String(value);
      bestScore = score;
    }
  });

  return { bestKey, bestValue, bestScore };
};

export const buildBindingSuggestions = ({
  jsonContent,
  variablesMap,
  selectedGenerators,
  source,
}: BindingSuggestionInput): BindingFieldRule[] => {
  const leaves = flattenJsonLeaves(jsonContent);

  return leaves.map((leaf) => {
    const { bestKey, bestValue, bestScore } = detectBestVariable(
      leaf.path,
      leaf.schema_type,
      variablesMap
    );

    const hasVariable = Boolean(bestKey && bestScore >= 0.78);
    const action = defaultActionFor(leaf.schema_type, leaf.value, hasVariable);
    const approved = hasVariable ? bestScore >= 0.92 : action === 'keep_template';

    return {
      json_path: leaf.path,
      schema_type: leaf.schema_type,
      suggested_variable_key: bestKey,
      variable_key: hasVariable ? bestKey : null,
      confidence: Number(bestScore.toFixed(2)),
      status: hasVariable
        ? (bestScore >= 0.92 ? 'matched' : 'suggested')
        : leaf.value === null || leaf.value === undefined
          ? 'generated'
          : 'template',
      action,
      approved,
      locked: false,
      generator_scope: selectedGenerators.length > 0 ? selectedGenerators : GENERATOR_SCOPE_DEFAULT,
      template_value_preview: stringifyPreview(leaf.value),
      variable_value_preview: bestValue,
    };
  });
};

export const hydrateBindingProfile = (
  name: string,
  rules: BindingFieldRule[],
  source: BindingProfileSource
): BindingProfilePayload => {
  const now = new Date().toISOString();

  return {
    name,
    source,
    rules,
    created_at: now,
    updated_at: now,
  };
};

export const normalizeBindingProfile = (profile: BindingProfile): BindingProfile => ({
  ...profile,
  rules: profile.rules.map((rule) => ({
    ...rule,
    generator_scope: Array.isArray(rule.generator_scope) ? rule.generator_scope : GENERATOR_SCOPE_DEFAULT,
  })),
});

const readBindingProfiles = (): BindingProfile[] => {
  if (typeof window === 'undefined') {
    return [];
  }

  try {
    const raw =
      window.localStorage.getItem(BINDING_STORAGE_KEY) ||
      window.localStorage.getItem(LEGACY_BINDING_STORAGE_KEY);
    if (!raw) {
      return [];
    }

    const parsed = JSON.parse(raw) as BindingProfile[];
    const normalized = Array.isArray(parsed) ? parsed.map(normalizeBindingProfile) : [];
    if (
      normalized.length > 0 &&
      !window.localStorage.getItem(BINDING_STORAGE_KEY) &&
      window.localStorage.getItem(LEGACY_BINDING_STORAGE_KEY)
    ) {
      window.localStorage.setItem(BINDING_STORAGE_KEY, JSON.stringify(normalized));
    }
    return normalized;
  } catch {
    return [];
  }
};

const writeBindingProfiles = (profiles: BindingProfile[]) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(BINDING_STORAGE_KEY, JSON.stringify(profiles));
};

export const listBindingProfiles = (): BindingProfile[] => readBindingProfiles();

export const getBindingProfile = (name: string): BindingProfile | undefined =>
  readBindingProfiles().find((profile) => profile.name === name);

export const saveBindingProfile = (profile: BindingProfilePayload): BindingProfile => {
  const profiles = readBindingProfiles();
  const nextProfile: BindingProfile = {
    ...profile,
    updated_at: new Date().toISOString(),
  };

  const index = profiles.findIndex((item) => item.name === profile.name);
  if (index >= 0) {
    profiles[index] = {
      ...profiles[index],
      ...nextProfile,
      created_at: profiles[index].created_at,
    };
  } else {
    profiles.push({
      ...nextProfile,
      created_at: profile.created_at || nextProfile.updated_at,
    });
  }

  writeBindingProfiles(profiles);
  return nextProfile;
};

export const deleteBindingProfile = (name: string): void => {
  const profiles = readBindingProfiles().filter((profile) => profile.name !== name);
  writeBindingProfiles(profiles);
};

export const extractVariableProfileNames = (selectedVariables: string[]) =>
  selectedVariables
    .filter((value) => value.startsWith('variables_file:'))
    .map((value) => value.replace('variables_file:', '').replace(/\.[^.]+$/, ''));
