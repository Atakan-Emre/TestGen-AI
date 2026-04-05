import type { Scenario, ScenarioGenerationJob, ScenarioMetadata } from '../api/types';
import type { JsonFile } from '../hooks/useJsonFiles';
import type { CsvFile } from '../hooks/useCsvFiles';
import type {
  BindingAutoResolveResult,
  BindingFieldRule,
  BindingGeneratorKey,
  BindingProfile,
  BindingProfileSummary,
  BindingValidationResult,
} from '../types/binding';
import type { VariableProfileInfo } from '../types/variables';
import type {
  GeneratedCaseSummary,
  GeneratorRunResult,
  TestGeneratorRequest,
} from '../hooks/testGenerator.utils';

export const DEMO_MODE_TITLE = 'GitHub Pages demo modu';
export const DEMO_MODE_DESCRIPTION =
  'Bu yayın statik örnek veri ile çalışır. Canlı backend çağrıları yapılmaz; dosya yükleme, silme ve kalıcı düzenleme işlemleri kapalıdır.';
export const DEMO_MUTATION_MESSAGE =
  'Bu işlem GitHub Pages demo modunda kapalı. Canlı kullanım için bir FastAPI backend deploy edilip VITE_API_URL tanımlanmalıdır.';

const DEMO_TIMESTAMP = '2026-04-05T19:15:26.967856Z';
const DEMO_SCENARIO_TEXT = `Hareket Seri (Movement Serial) alanı maksimum 3 karakterli olmalıdır.
Hareket Seri (Movement Serial) alanı benzersiz bir kimlik veya kod formatında olmalıdır.
Hareket Seri (Movement Serial) alanı doldurulması zorunludur.
Hareket Belge No (Movement Doc Nr) alanı maksimum 10 karakterli olmalıdır.
Hareket Belge No (Movement Doc Nr) alanı benzersiz bir kimlik veya kod formatında olmalıdır.
Hareket Belge No (Movement Doc Nr) alanı doldurulması zorunludur.
Hareket Belge No (Movement Doc Nr) alanı tekildir.
Tarih (Date) alanı geçerli bir tarih formatında olmalıdır.
Tarih (Date) alanı doldurulması zorunludur.
Saat (Time) alanı geçerli bir tarih formatında olmalıdır.
Saat (Time) alanı doldurulması zorunludur.
Hareket Belge Açıklama (Movement Doc Description) alanı maksimum 255 karakterli olmalıdır.
Hareket Belge Açıklama (Movement Doc Description) alanına sadece metin girişi yapılabilir.
Hareket Belge Açıklama (Movement Doc Description) alanı opsiyoneldir.
Hareket Para Birimi (Currency Description) alanı benzersiz bir kimlik veya kod formatında olmalıdır.
Hareket Para Birimi (Currency Description) alanı doldurulması zorunludur.
Kart Tipi (Card Type) alanı doldurulması zorunludur.
Kart Kod - Ad (Card Code - Name) alanı benzersiz bir kimlik veya kod formatında olmalıdır.
Kart Kod - Ad (Card Code - Name) alanı doldurulması zorunludur.
Muhasebeleşme Durumu (Accounting Status) alanı evet/hayır veya true/false tipinde olmalıdır.
Muhasebeleşme Durumu (Accounting Status) alanı doldurulması zorunludur.`;

const DEMO_CSV_CONTENT = `Alan Adı,Alan adı (İng),Tip,Boyut,Öndeğer,Zorunlu mu?,Tekil mi?
Hareket Seri,Movement Serial,Alfenumerik String,3,Standart A serisi,Zorunlu,
Hareket Belge No,Movement Doc Nr,Alfenumerik String,10,Seriye göre artar,Zorunlu,Tekil
Tarih,Date,Date,,İşlem tarihi,Zorunlu,
Saat,Time,Time,,İşlem saati,Zorunlu,
Hareket Belge Açıklama,Movement Doc Description,String,max 255,,Opsiyonel,
Hareket Para Birimi,Currency Description,Reference,,TRY,Zorunlu,
Kart Tipi,Card Type,Enum,,Müşteri,Zorunlu,
Muhasebeleşme Durumu,Accounting Status,Boolean,,Hayır,Zorunlu,`;

const DEMO_VARIABLE_CONTENT = `branchDocumentSeries.id=28052c8b-15a8-46d9-ba7f-86b848c60c3e
cardCurrencyDescription.id=a1af9bc0-8d79-4004-9298-8e720442e57a
checkNoteCaseCard.id=713f8a32-fd58-4ef6-8bef-940f09735752
currencyDescription.id=a1af9bc0-8d79-4004-9298-8e720442e57a
financeCard.id=5fbfdff0-7751-4510-b1ca-b20ecb3cfdcf
financeCardType=CUSTOMER
user.id=jplatformuser Admin`;

const DEMO_VARIABLE_MAP = {
  'branchDocumentSeries.id': '28052c8b-15a8-46d9-ba7f-86b848c60c3e',
  'cardCurrencyDescription.id': 'a1af9bc0-8d79-4004-9298-8e720442e57a',
  'checkNoteCaseCard.id': '713f8a32-fd58-4ef6-8bef-940f09735752',
  'currencyDescription.id': 'a1af9bc0-8d79-4004-9298-8e720442e57a',
  'financeCard.id': '5fbfdff0-7751-4510-b1ca-b20ecb3cfdcf',
  financeCardType: 'CUSTOMER',
  'user.id': 'jplatformuser Admin',
};

const DEMO_JSON_OBJECT = {
  accountingStatus: true,
  branchDocumentSeries: {
    documentClass: 'NONE',
    id: 'string',
    subDocumentClass: 'NONE',
  },
  cardCurrencyDescription: {
    id: 'string',
    numericCode: 'string',
    unit: 0,
  },
  cardCurrencyExchangeRate: 0,
  checkNoteCaseCard: {
    bankCard: {
      id: 'string',
    },
    financeCardType: 'CUSTOMER',
    id: 'string',
  },
  checkNoteCaseCardType: {
    id: 'string',
  },
  currencyDescription: {
    id: 'string',
    numericCode: 'string',
    unit: 0,
  },
  currencyExchangeRate: 0,
  documentDate: '2025-09-11T13:34:12.828Z',
  documentDescription: 'string',
  documentNumber: 'string',
  documentSpecialVariableValues: null,
  entityStatus: 'SAVED_TO_PHOENIX',
  externalId: 'string',
  financeCard: {
    bankCard: {
      id: 'string',
    },
    financeCardType: 'CUSTOMER',
    id: 'string',
  },
  financeCardType: 'CUSTOMER',
  id: 'string',
  relatedDocument: {
    branchDocumentSeries: {
      documentClass: 'NONE',
      id: 'string',
      subDocumentClass: 'NONE',
    },
    documentDate: '2025-09-11T13:34:12.828Z',
    documentDescription: 'string',
    documentNumber: 'string',
    id: 'string',
    subDocumentClass: 'NONE',
  },
  relatedInvoiceDocument: {
    branchDocumentSeries: {
      documentClass: 'NONE',
      id: 'string',
      subDocumentClass: 'NONE',
    },
    documentDate: '2025-09-11T13:34:12.828Z',
    documentDescription: 'string',
    documentNumber: 'string',
    id: 'string',
    subDocumentClass: 'NONE',
  },
  subDocumentClass: 'NONE',
  turnover: true,
  user: {
    active: true,
    description: 'string',
    id: 'string',
    username: 'string',
  },
};

export const demoScenarioMetadata: ScenarioMetadata = {
  scenario_name: 'test',
  source_csv: 'example.csv',
  generator_type: 'nlp_hybrid',
  generated_at: DEMO_TIMESTAMP,
  field_count: 43,
  required_count: 34,
  optional_count: 9,
  unique_count: 2,
  average_confidence: 0.87,
  semantic_tags: ['person', 'document', 'check', 'card', 'date', 'currency'],
  type_distribution: [
    { type: 'id', count: 12 },
    { type: 'string', count: 9 },
    { type: 'date', count: 6 },
    { type: 'enum', count: 6 },
    { type: 'number', count: 6 },
    { type: 'bool', count: 4 },
  ],
  fields: [
    {
      field_name_tr: 'Hareket Seri',
      field_name_en: 'Movement Serial',
      field_type: 'id',
      raw_type: 'Alfenumerik String',
      required: true,
      optional: false,
      unique: false,
      max_len: 3,
      min_len: null,
      pattern: null,
      enum_values: [],
      semantic_tags: ['serial', 'document'],
      confidence: 0.97,
    },
    {
      field_name_tr: 'Hareket Belge No',
      field_name_en: 'Movement Doc Nr',
      field_type: 'id',
      raw_type: 'Alfenumerik String',
      required: true,
      optional: false,
      unique: true,
      max_len: 10,
      min_len: null,
      pattern: null,
      enum_values: [],
      semantic_tags: ['document', 'number'],
      confidence: 0.97,
    },
    {
      field_name_tr: 'Tarih',
      field_name_en: 'Date',
      field_type: 'date',
      raw_type: 'Date',
      required: true,
      optional: false,
      unique: false,
      max_len: null,
      min_len: null,
      pattern: null,
      enum_values: [],
      semantic_tags: ['date'],
      confidence: 0.98,
    },
    {
      field_name_tr: 'Hareket Belge Açıklama',
      field_name_en: 'Movement Doc Description',
      field_type: 'string',
      raw_type: 'String',
      required: false,
      optional: true,
      unique: false,
      max_len: 255,
      min_len: null,
      pattern: null,
      enum_values: [],
      semantic_tags: ['description'],
      confidence: 0.89,
    },
  ],
};

export const demoCsvFiles: CsvFile[] = [
  {
    id: 1,
    name: 'example.csv',
    content: DEMO_CSV_CONTENT,
    size: DEMO_CSV_CONTENT.length,
    created_at: DEMO_TIMESTAMP,
    updated_at: DEMO_TIMESTAMP,
    source: 'repo-sample',
  },
];

export const demoJsonFiles: JsonFile[] = [
  {
    id: 1,
    name: 'Example-Header.json',
    content: DEMO_JSON_OBJECT,
    size: JSON.stringify(DEMO_JSON_OBJECT).length,
    created_at: DEMO_TIMESTAMP,
    updated_at: DEMO_TIMESTAMP,
    type: 'header',
    source: 'repo-sample',
  },
];

export const demoVariableFiles = [
  {
    id: 1,
    name: 'variablesHeader.txt',
    size: DEMO_VARIABLE_CONTENT.length,
    created_at: Math.floor(new Date(DEMO_TIMESTAMP).getTime() / 1000),
    updated_at: Math.floor(new Date(DEMO_TIMESTAMP).getTime() / 1000),
    type: 'txt',
    content: DEMO_VARIABLE_CONTENT,
  },
];

export const demoVariableProfiles: VariableProfileInfo[] = [
  {
    name: 'variablesHeader',
    format: 'txt',
    updatedAt: DEMO_TIMESTAMP,
    sizeBytes: DEMO_VARIABLE_CONTENT.length,
  },
];

export const demoScenarios: Scenario[] = [
  {
    id: 'test',
    name: 'test',
    full_name: '/app/data/output/test_scenarios/test.txt',
    file_path: '/app/data/output/test_scenarios/test.txt',
    filename: 'test.txt',
    date: '2026-04-05',
    created_at: DEMO_TIMESTAMP,
    updated_at: DEMO_TIMESTAMP,
    size: DEMO_SCENARIO_TEXT.length,
    metadata: demoScenarioMetadata,
  },
];

const DEMO_CASE_COUNTS = {
  bsc: 1,
  ngi: 21,
  ngv: 0,
  opt: 4,
} as const;

const DEMO_TOTAL_CASES =
  DEMO_CASE_COUNTS.bsc +
  DEMO_CASE_COUNTS.ngi +
  DEMO_CASE_COUNTS.ngv +
  DEMO_CASE_COUNTS.opt;

export const demoDashboardSummary = {
  status: 'healthy',
  generated_at: DEMO_TIMESTAMP,
  counts: {
    csv_files: demoCsvFiles.length,
    json_files: demoJsonFiles.length,
    variable_files: demoVariableFiles.length,
    input_files: demoCsvFiles.length + demoJsonFiles.length + demoVariableFiles.length,
    scenarios: demoScenarios.length,
    test_suites: 1,
    test_cases: DEMO_TOTAL_CASES,
  },
  input_breakdown: [
    { key: 'csv', label: 'CSV', count: demoCsvFiles.length },
    { key: 'json', label: 'JSON', count: demoJsonFiles.length },
    { key: 'variables', label: 'Variables', count: demoVariableFiles.length },
  ],
  test_types: [
    { key: 'bsc', label: 'BSC', suite_count: 1, case_count: DEMO_CASE_COUNTS.bsc },
    { key: 'ngi', label: 'NGI', suite_count: 1, case_count: DEMO_CASE_COUNTS.ngi },
    { key: 'ngv', label: 'NGV', suite_count: 1, case_count: DEMO_CASE_COUNTS.ngv },
    { key: 'opt', label: 'OPT', suite_count: 1, case_count: DEMO_CASE_COUNTS.opt },
  ],
  recent_scenarios: [
    {
      id: 'test',
      name: 'test',
      date: '2026-04-05',
      filename: 'test.txt',
      updated_at: DEMO_TIMESTAMP,
      size: DEMO_SCENARIO_TEXT.length,
    },
  ],
  recent_tests: [
    {
      name: 'test',
      created_at: DEMO_TIMESTAMP,
      updated_at: DEMO_TIMESTAMP,
      total_files: DEMO_TOTAL_CASES,
      types: [
        { key: 'bsc', label: 'BSC', count: DEMO_CASE_COUNTS.bsc },
        { key: 'ngi', label: 'NGI', count: DEMO_CASE_COUNTS.ngi },
        { key: 'ngv', label: 'NGV', count: DEMO_CASE_COUNTS.ngv },
        { key: 'opt', label: 'OPT', count: DEMO_CASE_COUNTS.opt },
      ],
    },
  ],
};

export const demoBindingRules: BindingFieldRule[] = [
  {
    json_path: 'branchDocumentSeries.id',
    schema_type: 'id',
    suggested_variable_key: 'branchDocumentSeries.id',
    variable_key: 'branchDocumentSeries.id',
    confidence: 0.99,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: DEMO_VARIABLE_MAP['branchDocumentSeries.id'],
  },
  {
    json_path: 'cardCurrencyDescription.id',
    schema_type: 'id',
    suggested_variable_key: 'cardCurrencyDescription.id',
    variable_key: 'cardCurrencyDescription.id',
    confidence: 0.99,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: DEMO_VARIABLE_MAP['cardCurrencyDescription.id'],
  },
  {
    json_path: 'currencyDescription.id',
    schema_type: 'id',
    suggested_variable_key: 'currencyDescription.id',
    variable_key: 'currencyDescription.id',
    confidence: 0.99,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: DEMO_VARIABLE_MAP['currencyDescription.id'],
  },
  {
    json_path: 'financeCard.id',
    schema_type: 'id',
    suggested_variable_key: 'financeCard.id',
    variable_key: 'financeCard.id',
    confidence: 0.98,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: DEMO_VARIABLE_MAP['financeCard.id'],
  },
  {
    json_path: 'financeCardType',
    schema_type: 'enum',
    suggested_variable_key: 'financeCardType',
    variable_key: 'financeCardType',
    confidence: 0.98,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'opt'],
    template_value_preview: 'CUSTOMER',
    variable_value_preview: DEMO_VARIABLE_MAP.financeCardType,
  },
  {
    json_path: 'user.id',
    schema_type: 'id',
    suggested_variable_key: 'user.id',
    variable_key: 'user.id',
    confidence: 0.96,
    status: 'matched',
    action: 'use_variable',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: DEMO_VARIABLE_MAP['user.id'],
  },
  {
    json_path: 'documentDescription',
    schema_type: 'string',
    suggested_variable_key: null,
    variable_key: null,
    confidence: 0.83,
    status: 'template',
    action: 'keep_template',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: null,
  },
  {
    json_path: 'documentNumber',
    schema_type: 'id',
    suggested_variable_key: null,
    variable_key: null,
    confidence: 0.79,
    status: 'generated',
    action: 'generate_dynamic',
    approved: true,
    locked: false,
    generator_scope: ['bsc', 'ngi', 'ngv', 'opt'],
    template_value_preview: 'string',
    variable_value_preview: null,
  },
  {
    json_path: 'entityStatus',
    schema_type: 'enum',
    suggested_variable_key: null,
    variable_key: null,
    confidence: 0.91,
    status: 'template',
    action: 'keep_template',
    approved: true,
    locked: true,
    generator_scope: ['bsc', 'opt'],
    template_value_preview: 'SAVED_TO_PHOENIX',
    variable_value_preview: null,
  },
];

export const demoBindingProfile: BindingProfile = {
  name: 'binding_auto_test_variablesheader_bsc_ngi_ngv_opt',
  source: {
    scenario_name: 'test',
    scenario_id: 'test',
    json_file_id: 1,
    json_file_name: 'Example-Header.json',
    variable_profiles: ['variablesHeader'],
  },
  rules: demoBindingRules,
  created_at: DEMO_TIMESTAMP,
  updated_at: DEMO_TIMESTAMP,
};

export const demoBindingProfileSummary: BindingProfileSummary = {
  name: demoBindingProfile.name,
  json_file_id: 1,
  variables_profile: 'variablesHeader',
  description: 'GitHub Pages demo otomatik binding profili',
  binding_count: demoBindingRules.length,
  size_bytes: JSON.stringify(demoBindingProfile).length,
  updated_at: DEMO_TIMESTAMP,
};

export const demoAutoResolveResult: BindingAutoResolveResult = {
  profile_name: demoBindingProfile.name,
  review_recommended: true,
  summary: {
    total_fields: 49,
    matched_fields: 9,
    suggested_fields: 0,
    generated_fields: 1,
    template_fields: 39,
    bound_fields: 9,
    approved_fields: 48,
    match_ratio: 0.184,
    average_confidence: 0.349,
    min_confidence: 0,
    review_recommended: true,
    review_reasons: ['generated_fields_present', 'low_match_ratio'],
  },
  suggestion: {
    json_file_id: 1,
    variables_profile: 'variablesHeader',
    total_fields: 49,
    matched_fields: 9,
    unmatched_fields: 40,
    fields: demoBindingRules,
    generated_at: DEMO_TIMESTAMP,
  },
  saved_profile: demoBindingProfile,
};

const demoCaseCatalog: Record<string, GeneratedCaseSummary[]> = {
  bsc: [
    {
      file_path: '/demo/test/bsc/bsc_test.json',
      file_name: 'bsc_test.json',
      description: 'BSC test senaryosu - test (18 zorunlu alan)',
      scenario_type: 'BSC',
      expected_result: 'SUCCESS',
    },
  ],
  ngi: [
    {
      file_path: '/demo/test/ngi/ngi_test_01.json',
      file_name: 'ngi_test_01.json',
      description: "Alan 'currencyDescription.id' için geçersiz para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'currencyDescription.id' için geçersiz değer: invalid-currency-id",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_02.json',
      file_name: 'ngi_test_02.json',
      description: "Alan 'currencyDescription.id' için boş para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'currencyDescription.id' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_03.json',
      file_name: 'ngi_test_03.json',
      description: "Alan 'currencyDescription.id' için yanlış tipte para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'currencyDescription.id' için geçersiz değer: 12345",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_04.json',
      file_name: 'ngi_test_04.json',
      description: "Alan 'financeCardType' için desteklenmeyen enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCardType' için geçersiz değer: __INVALID_ENUM__",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_05.json',
      file_name: 'ngi_test_05.json',
      description: "Alan 'financeCardType' için boş enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCardType' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_06.json',
      file_name: 'ngi_test_06.json',
      description: "Alan 'financeCardType' için yanlış tipte enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCardType' için geçersiz değer: 999",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_07.json',
      file_name: 'ngi_test_07.json',
      description: "Alan 'documentSpecialVariableValues' için desteklenmeyen enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'documentSpecialVariableValues' için geçersiz değer: __INVALID_ENUM__",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_08.json',
      file_name: 'ngi_test_08.json',
      description: "Alan 'documentSpecialVariableValues' için boş enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'documentSpecialVariableValues' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_09.json',
      file_name: 'ngi_test_09.json',
      description: "Alan 'documentSpecialVariableValues' için yanlış tipte enum değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'documentSpecialVariableValues' için geçersiz değer: 999",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_10.json',
      file_name: 'ngi_test_10.json',
      description: "Alan 'user.id' için geçersiz referans kimliği testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'user.id' için geçersiz değer: not-a-uuid",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_11.json',
      file_name: 'ngi_test_11.json',
      description: "Alan 'user.id' için boş referans değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'user.id' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_12.json',
      file_name: 'ngi_test_12.json',
      description: "Alan 'user.id' için yanlış tipte referans değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'user.id' için geçersiz değer: 12345",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_13.json',
      file_name: 'ngi_test_13.json',
      description: "Alan 'financeCard.financeCardType' için maksimum uzunluğu aşan değer testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCard.financeCardType' için geçersiz değer: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_14.json',
      file_name: 'ngi_test_14.json',
      description: "Alan 'financeCard.financeCardType' için boş metin testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCard.financeCardType' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_15.json',
      file_name: 'ngi_test_15.json',
      description: "Alan 'financeCard.financeCardType' için özel karakterlerden oluşan metin testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'financeCard.financeCardType' için geçersiz değer: !@#$%^&*()",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_16.json',
      file_name: 'ngi_test_16.json',
      description: "Alan 'cardCurrencyDescription.id' için geçersiz para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'cardCurrencyDescription.id' için geçersiz değer: invalid-currency-id",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_17.json',
      file_name: 'ngi_test_17.json',
      description: "Alan 'cardCurrencyDescription.id' için boş para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'cardCurrencyDescription.id' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_18.json',
      file_name: 'ngi_test_18.json',
      description: "Alan 'cardCurrencyDescription.id' için yanlış tipte para birimi referansı testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'cardCurrencyDescription.id' için geçersiz değer: 12345",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_19.json',
      file_name: 'ngi_test_19.json',
      description: "Alan 'checkNoteCaseCard.financeCardType' için maksimum uzunluğu aşan değer testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'checkNoteCaseCard.financeCardType' için geçersiz değer: XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_20.json',
      file_name: 'ngi_test_20.json',
      description: "Alan 'checkNoteCaseCard.financeCardType' için boş kişi değeri testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'checkNoteCaseCard.financeCardType' için geçersiz değer: ",
    },
    {
      file_path: '/demo/test/ngi/ngi_test_21.json',
      file_name: 'ngi_test_21.json',
      description: "Alan 'checkNoteCaseCard.financeCardType' için isim alanı için sayısal değer testi",
      scenario_type: 'NGI',
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'checkNoteCaseCard.financeCardType' için geçersiz değer: 123456",
    },
  ],
  ngv: [],
  opt: [
    {
      file_path: '/demo/test/opt/opt_test_01.json',
      file_name: 'opt_test_01.json',
      description: 'Tüm opsiyonel alanlar dolu senaryo',
      scenario_type: 'OPT',
      expected_result: 'SUCCESS',
    },
    {
      file_path: '/demo/test/opt/opt_test_02.json',
      file_name: 'opt_test_02.json',
      description: 'Opsiyonel alanlar boş bırakılmış senaryo',
      scenario_type: 'OPT',
      expected_result: 'SUCCESS',
    },
    {
      file_path: '/demo/test/opt/opt_test_03.json',
      file_name: 'opt_test_03.json',
      description: 'Karışık opsiyonel kombinasyon senaryosu',
      scenario_type: 'OPT',
      expected_result: 'SUCCESS',
    },
    {
      file_path: '/demo/test/opt/opt_test_04.json',
      file_name: 'opt_test_04.json',
      description: 'Sadece Çekin Borçlusu dolu senaryo',
      scenario_type: 'OPT',
      expected_result: 'SUCCESS',
    },
  ],
};

const demoCaseContent: Record<string, string> = {
  bsc: JSON.stringify(
    {
      created_at: DEMO_TIMESTAMP,
      description: 'BSC test senaryosu - test (18 zorunlu alan)',
      expected_result: 'SUCCESS',
      generated_at: DEMO_TIMESTAMP,
      mandatory_fields_count: 18,
      scenario_type: 'BSC',
      test_data: DEMO_JSON_OBJECT,
      test_name: 'test',
      variables_count: 48,
      version: '1.0',
    },
    null,
    2
  ),
  ngi: JSON.stringify(
    {
      scenario_type: 'NGI',
      description: "Alan 'currencyDescription.id' için geçersiz para birimi referansı testi",
      test_data: DEMO_JSON_OBJECT,
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'currencyDescription.id' için geçersiz değer: invalid-currency-id",
    },
    null,
    2
  ),
  ngv: JSON.stringify(
    {
      scenario_type: 'NGV',
      description: "Tekil alan 'Hareket Belge No' için tekrarlı değer testi",
      test_data: [DEMO_JSON_OBJECT, DEMO_JSON_OBJECT],
      expected_result: 'VALIDATION_ERROR',
      expected_message: "Alan 'relatedDocument.branchDocumentSeries.id' için tekrarlı değer hatası: DOC-0001",
    },
    null,
    2
  ),
  opt: JSON.stringify(
    {
      scenario_type: 'OPT',
      description: 'Tüm opsiyonel alanlar dolu senaryo',
      test_data: DEMO_JSON_OBJECT,
      expected_result: 'SUCCESS',
    },
    null,
    2
  ),
};

export const demoTestDirectories = [
  {
    name: 'test',
    created_at: DEMO_TIMESTAMP,
  },
];

export const demoTestGroups = [
  {
    test_name: 'test',
    created_at: DEMO_TIMESTAMP,
    files: (['bsc', 'ngi', 'ngv', 'opt'] as const).flatMap((type) =>
      demoCaseCatalog[type].map((item) => ({
        name: item.file_name || `${type}_sample.json`,
        type,
        created_at: DEMO_TIMESTAMP,
        description: item.description,
        scenario_type: item.scenario_type,
        expected_result: item.expected_result,
        expected_message: item.expected_message,
        file_path: item.file_path,
        test_name: 'test',
      }))
    ),
  },
];

export const getDemoVariableFileContent = (name: string) => {
  if (name === 'variablesHeader.txt' || name === 'variablesHeader') {
    return DEMO_VARIABLE_CONTENT;
  }
  throw new Error(`Demo variables profili bulunamadı: ${name}`);
};

export const getDemoScenarioDetail = (filename: string) => {
  if (!filename.includes('test')) {
    return {
      content: DEMO_SCENARIO_TEXT,
      metadata: {
        ...demoScenarioMetadata,
        scenario_name: filename.replace(/\.txt$/, ''),
      },
    };
  }

  return {
    content: DEMO_SCENARIO_TEXT,
    metadata: demoScenarioMetadata,
  };
};

export const getDemoJsonFileById = (id: number) =>
  demoJsonFiles.find((file) => file.id === id) || demoJsonFiles[0];

export const getDemoBindingValidationResult = (): BindingValidationResult => ({
  scenario_id: 'test',
  scenario_path: demoScenarios[0].full_name || '',
  json_file_id: 1,
  variables_profile: 'variablesHeader',
  binding_profile_name: demoBindingProfile.name,
  binding_summary: demoAutoResolveResult.summary,
  auto_binding: demoAutoResolveResult,
  validation_name: 'test_binding_validation',
  validated_at: DEMO_TIMESTAMP,
  generator_results: {
    bsc: {
      generator: 'bsc',
      success: true,
      result_count: 1,
      output_files: [demoCaseCatalog.bsc[0].file_path || ''],
      message: 'Demo BSC çıktısı hazır',
      duration_ms: 180,
    },
    ngi: {
      generator: 'ngi',
      success: true,
      result_count: DEMO_CASE_COUNTS.ngi,
      output_files: demoCaseCatalog.ngi.map((item) => item.file_path || ''),
      message: 'Demo NGI çıktısı hazır',
      duration_ms: 220,
    },
    ngv: {
      generator: 'ngv',
      success: true,
      result_count: DEMO_CASE_COUNTS.ngv,
      output_files: demoCaseCatalog.ngv.map((item) => item.file_path || ''),
      message: 'Bu örnek veri seti için NGV çıktısı üretilmedi',
      duration_ms: 205,
    },
    opt: {
      generator: 'opt',
      success: true,
      result_count: DEMO_CASE_COUNTS.opt,
      output_files: demoCaseCatalog.opt.map((item) => item.file_path || ''),
      message: 'Demo OPT çıktısı hazır',
      duration_ms: 170,
    },
  },
  overall_success: true,
  report_path: '/demo/reports/test_binding_validation.json',
});

export const buildDemoGeneratorResult = (
  generatorType: string,
  request: TestGeneratorRequest
): GeneratorRunResult => {
  const normalizedType = generatorType.toLowerCase();
  const baseCases = demoCaseCatalog[normalizedType] || [];
  const generatedCases = baseCases.map((item) => ({
    ...item,
    file_path: item.file_path?.replace('/demo/test/', `/demo/${request.test_name}/`),
  }));

  return {
    type: normalizedType,
    success: true,
    message: `${normalizedType.toUpperCase()} demo çıktısı hazır`,
    test_result: {
      demo: true,
      test_name: request.test_name,
    },
    generated_cases: generatedCases,
    generated_count: generatedCases.length,
    variables_profile: request.selected_variables[0]?.replace('variables_file:', '').replace(/\.[^.]+$/, ''),
  };
};

export const getDemoTestFileContent = (type: string) => {
  const normalizedType = type.toLowerCase();
  return demoCaseContent[normalizedType] || '{}';
};

export const buildDemoScenarioJob = (name: string, csvFileName: string): ScenarioGenerationJob => ({
  job_id: `demo-${name.toLowerCase().replace(/[^a-z0-9]+/gi, '-')}`,
  request: {
    name,
    csv_file_name: csvFileName,
    generator_type: 'nlp_hybrid',
  },
  status: 'completed',
  progress: 1,
  current_stage: 'completed',
  logs: [
    {
      timestamp: DEMO_TIMESTAMP,
      level: 'info',
      message: 'GitHub Pages demo modunda örnek senaryo bundle yüklendi.',
    },
    {
      timestamp: DEMO_TIMESTAMP,
      level: 'info',
      message: `${csvFileName} için semantic alan profili ve senaryo metni hazırlandı.`,
    },
  ],
  result: {
    message: 'Demo senaryo bundle hazır',
    scenarios: DEMO_SCENARIO_TEXT.split('\n').slice(0, 12),
    scenario_file: `${name}_demo_bundle.txt`,
    summary: {
      ...demoScenarioMetadata,
      scenario_name: name,
      source_csv: csvFileName,
    },
  },
  error: null,
  created_at: DEMO_TIMESTAMP,
  started_at: DEMO_TIMESTAMP,
  completed_at: DEMO_TIMESTAMP,
  updated_at: DEMO_TIMESTAMP,
});
