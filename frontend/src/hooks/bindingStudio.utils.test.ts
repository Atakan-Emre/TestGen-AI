import {
  buildBindingSuggestions,
  deleteBindingProfile,
  extractVariableProfileNames,
  getBindingProfile,
  listBindingProfiles,
  saveBindingProfile,
} from './bindingStudio.utils';

describe('bindingStudio utils', () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it('extracts variable profile names from selected files', () => {
    expect(extractVariableProfileNames(['variables_file:variablesHeader.txt', 'variables_file:other.json'])).toEqual([
      'variablesHeader',
      'other',
    ]);
  });

  it('builds binding suggestions from JSON and variable map', () => {
    const suggestions = buildBindingSuggestions({
      jsonContent: {
        currentAccount: {
          financeCardType: null,
        },
        documentDate: null,
        documentDescription: 'template',
      },
      variablesMap: {
        'currentAccount.financeCardType': 'CUSTOMER',
        documentDate: '2026-04-04',
      },
      selectedGenerators: ['bsc', 'ngi', 'ngv', 'opt'],
      source: {
        scenario_name: 'demo',
        scenario_id: 1,
        json_file_id: 2,
        json_file_name: 'example.json',
        variable_profiles: ['variablesHeader'],
      },
    });

    const financeRule = suggestions.find((rule) => rule.json_path === 'currentAccount.financeCardType');
    const dateRule = suggestions.find((rule) => rule.json_path === 'documentDate');
    const descRule = suggestions.find((rule) => rule.json_path === 'documentDescription');

    expect(financeRule?.variable_key).toBe('currentAccount.financeCardType');
    expect(financeRule?.action).toBe('use_variable');
    expect(financeRule?.approved).toBe(true);
    expect(dateRule?.variable_key).toBe('documentDate');
    expect(dateRule?.confidence).toBeGreaterThan(0.6);
    expect(descRule?.action).toBe('keep_template');
  });

  it('persists binding profiles in local storage', () => {
    saveBindingProfile({
      name: 'binding-demo',
      source: {
        scenario_name: 'demo',
        scenario_id: 1,
        json_file_id: 2,
        json_file_name: 'example.json',
        variable_profiles: ['variablesHeader'],
      },
      rules: [],
      created_at: '2026-04-04T00:00:00.000Z',
      updated_at: '2026-04-04T00:00:00.000Z',
    });

    expect(listBindingProfiles()).toHaveLength(1);
    expect(getBindingProfile('binding-demo')?.name).toBe('binding-demo');

    deleteBindingProfile('binding-demo');
    expect(listBindingProfiles()).toHaveLength(0);
  });
});

