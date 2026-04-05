import {
  GENERATOR_DEFINITIONS,
  buildTestPayload,
  extractVariablesProfile,
  generatorUsesVariables,
  normalizeGeneratorResult,
  summarizeGeneratorRuns,
} from './testGenerator.utils';

describe('testGenerator utils', () => {
  const baseRequest = {
    test_type: 'bsc',
    scenario_path: '/app/data/output/test_scenarios/example.txt',
    test_name: 'demo-suite',
    json_file_id: 3,
    selected_variables: ['variables_file:variablesHeader.txt'],
    binding_profile: 'binding_demo',
  };

  const objectBindingRequest = {
    ...baseRequest,
    binding_profile: {
      name: 'binding_demo_object',
      source: {
        scenario_name: 'demo',
        scenario_id: 1,
        json_file_id: 3,
        json_file_name: 'example.json',
        variable_profiles: ['variablesHeader'],
      },
      rules: [],
      created_at: '2026-04-04T00:00:00.000Z',
      updated_at: '2026-04-04T00:00:00.000Z',
    },
  };

  it('extracts variables profile from selected files', () => {
    expect(extractVariablesProfile(baseRequest.selected_variables)).toBe('variablesHeader');
    expect(extractVariablesProfile([])).toBeUndefined();
  });

  it('builds BSC payload with selected variables intact', () => {
    expect(buildTestPayload('bsc', baseRequest)).toEqual({
      ...baseRequest,
      test_type: 'bsc',
      binding_profile: baseRequest.binding_profile,
    });
  });

  it('builds OPT payload with variables profile', () => {
    expect(buildTestPayload('opt', baseRequest)).toEqual({
      scenario_id: baseRequest.scenario_path,
      test_name: baseRequest.test_name,
      json_files: [baseRequest.json_file_id],
      variables_profile: 'variablesHeader',
      binding_profile: baseRequest.binding_profile,
    });
  });

  it('stringifies object binding profiles when present', () => {
    expect(buildTestPayload('bsc', objectBindingRequest)).toEqual({
      ...objectBindingRequest,
      test_type: 'bsc',
      binding_profile: JSON.stringify(objectBindingRequest.binding_profile),
    });

    expect(buildTestPayload('opt', objectBindingRequest)).toEqual({
      scenario_id: objectBindingRequest.scenario_path,
      test_name: objectBindingRequest.test_name,
      json_files: [objectBindingRequest.json_file_id],
      variables_profile: 'variablesHeader',
      binding_profile: JSON.stringify(objectBindingRequest.binding_profile),
    });
  });

  it('normalizes raw API result into generator result', () => {
    expect(
      normalizeGeneratorResult('ngi', { message: 'ok', result: [{ file_path: 'ngi.json' }] }, [])
    ).toEqual({
      type: 'ngi',
      success: true,
      message: 'ok',
      test_result: { file_path: 'ngi.json' },
      error: undefined,
      variables_profile: undefined,
      generated_cases: [
        {
          file_path: 'ngi.json',
          file_name: 'ngi.json',
          description: undefined,
          scenario_type: undefined,
          expected_result: undefined,
          expected_message: undefined,
        },
      ],
      generated_count: 1,
    });
  });

  it('marks all active generators as variables-aware', () => {
    expect(generatorUsesVariables('bsc')).toBe(true);
    expect(generatorUsesVariables('opt')).toBe(true);
    expect(generatorUsesVariables('ngi')).toBe(true);
    expect(generatorUsesVariables('ngv')).toBe(true);
  });

  it('exposes four generator definitions with operational focus labels', () => {
    expect(GENERATOR_DEFINITIONS).toHaveLength(4);
    expect(GENERATOR_DEFINITIONS.map((item) => item.key)).toEqual(['bsc', 'ngi', 'ngv', 'opt']);
    expect(GENERATOR_DEFINITIONS.every((item) => item.focus.length > 0)).toBe(true);
  });

  it('summarizes run results with success and failure counts', () => {
    expect(
      summarizeGeneratorRuns([
        { type: 'bsc', success: true, message: 'ok', generated_cases: [], generated_count: 0 },
        { type: 'ngi', success: false, message: 'fail', generated_cases: [], generated_count: 0 },
      ])
    ).toEqual({
      total: 2,
      successCount: 1,
      failureCount: 1,
      successRate: 50,
      successTypes: ['bsc'],
      failureTypes: ['ngi'],
    });
  });
});
