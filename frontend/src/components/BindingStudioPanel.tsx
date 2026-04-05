import React, { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Checkbox,
  Col,
  Input,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import {
  CheckSquareOutlined,
  DeleteOutlined,
  LockOutlined,
  ReloadOutlined,
  SaveOutlined,
  SearchOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import type { JsonFile } from '../hooks/useJsonFiles';
import type { BindingGeneratorKey, BindingFieldRule } from '../types/binding';
import { extractVariableProfileNames } from '../hooks/bindingStudio.utils';
import { useBindingStudio } from '../hooks/useBindingStudio';
import type { BindingAction } from '../types/binding';

const ACTION_OPTIONS: Array<{ value: BindingAction; label: string }> = [
  { value: 'use_variable', label: 'Variables kullan' },
  { value: 'generate_dynamic', label: 'Dinamik üret' },
  { value: 'keep_template', label: 'Şablonu koru' },
  { value: 'do_not_touch', label: 'Dokunma' },
  { value: 'force_null', label: 'Boş bırak' },
];

const SCHEMA_COLORS: Record<string, string> = {
  id: 'blue',
  uuid: 'geekblue',
  date: 'gold',
  numeric: 'purple',
  string: 'green',
  boolean: 'cyan',
  currency: 'orange',
  object: 'default',
  array: 'default',
  unknown: 'default',
};

const SCHEMA_LABELS: Record<string, string> = {
  id: 'Kimlik',
  uuid: 'UUID',
  date: 'Tarih',
  numeric: 'Sayısal',
  number: 'Sayısal',
  string: 'Metin',
  boolean: 'Mantıksal',
  bool: 'Mantıksal',
  currency: 'Para Birimi',
  object: 'Nesne',
  array: 'Dizi',
  unknown: 'Bilinmiyor',
};

const STATUS_COLORS: Record<string, string> = {
  matched: 'green',
  suggested: 'blue',
  generated: 'gold',
  template: 'default',
  ignored: 'red',
  unmapped: 'default',
};

const STATUS_LABELS: Record<string, string> = {
  matched: 'Eşleşti',
  suggested: 'Öneri',
  generated: 'Dinamik',
  template: 'Şablon',
  ignored: 'Yoksay',
  unmapped: 'Eşleşmedi',
};

interface BindingStudioPanelProps {
  jsonFile: JsonFile | null;
  selectedScenarioName?: string;
  selectedScenarioId?: number | string | null;
  selectedVariables: string[];
  selectedGenerators: BindingGeneratorKey[];
  onBindingProfileNameChange?: (name: string | null) => void;
}

const buildDefaultProfileName = (
  scenarioName?: string,
  jsonFile?: JsonFile | null
) => {
  const base = scenarioName || jsonFile?.name || 'binding-profile';
  return `binding_${base.replace(/[^a-z0-9._-]+/gi, '_').toLowerCase()}`;
};

const parseJsonContent = (jsonFile: JsonFile | null) => {
  if (!jsonFile?.content) {
    return null;
  }

  if (typeof jsonFile.content === 'object') {
    return jsonFile.content;
  }

  if (typeof jsonFile.content !== 'string') {
    return null;
  }

  try {
    return JSON.parse(jsonFile.content);
  } catch {
    return null;
  }
};

const formatPreview = (value?: string | null) => {
  if (!value) {
    return '-';
  }

  return value.length > 28 ? `${value.slice(0, 25)}...` : value;
};

export const BindingStudioPanel: React.FC<BindingStudioPanelProps> = ({
  jsonFile,
  selectedScenarioName,
  selectedScenarioId,
  selectedVariables,
  selectedGenerators,
  onBindingProfileNameChange,
}) => {
  const [messageApi, contextHolder] = message.useMessage();
  const [searchText, setSearchText] = useState('');
  const [actionFilter, setActionFilter] = useState<string | undefined>(undefined);
  const [savedProfileToLoad, setSavedProfileToLoad] = useState<string | undefined>(undefined);

  const jsonContent = useMemo(() => parseJsonContent(jsonFile), [jsonFile]);
  const selectedVariableProfiles = useMemo(
    () => extractVariableProfileNames(selectedVariables),
    [selectedVariables]
  );
  const source = useMemo(
    () => ({
      scenario_name: selectedScenarioName || null,
      scenario_id: selectedScenarioId || null,
      json_file_id: jsonFile?.id || null,
      json_file_name: jsonFile?.name || null,
      variable_profiles: selectedVariableProfiles,
    }),
    [jsonFile, selectedScenarioId, selectedScenarioName, selectedVariableProfiles]
  );

  const {
    rules,
    loading,
    error,
    savedProfiles,
    selectedProfileName,
    profileNameDraft,
    setProfileNameDraft,
    setSelectedProfileName,
    updateRule,
    saveCurrentProfile,
    loadSelectedProfile,
    deleteProfile,
    resetSuggestions,
  } = useBindingStudio({
    jsonContent,
    selectedVariables,
    selectedGenerators,
    source,
  });

  useEffect(() => {
    if (!onBindingProfileNameChange) {
      return;
    }

    onBindingProfileNameChange(selectedProfileName || null);
  }, [onBindingProfileNameChange, selectedProfileName]);

  const filteredRules = useMemo(() => {
    const search = searchText.trim().toLowerCase();

    return rules.filter((rule) => {
      const matchesSearch =
        !search ||
        rule.json_path.toLowerCase().includes(search) ||
        rule.schema_type.toLowerCase().includes(search) ||
        (rule.variable_key || '').toLowerCase().includes(search) ||
        (rule.suggested_variable_key || '').toLowerCase().includes(search);
      const matchesAction = !actionFilter || rule.action === actionFilter;
      return matchesSearch && matchesAction;
    });
  }, [actionFilter, rules, searchText]);

  const summary = useMemo(() => {
    const approved = rules.filter((rule) => rule.approved).length;
    const locked = rules.filter((rule) => rule.locked).length;
    const matched = rules.filter((rule) => Boolean(rule.variable_key)).length;
    return { approved, locked, matched, total: rules.length };
  }, [rules]);

  const handleSave = async () => {
    try {
      const saved = await saveCurrentProfile(profileNameDraft || buildDefaultProfileName(selectedScenarioName, jsonFile));
      messageApi.success(`Binding profili kaydedildi: ${saved.name}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Binding profili kaydedilemedi';
      messageApi.error(errorMessage);
    }
  };

  const handleLoad = async () => {
    if (!savedProfileToLoad) {
      messageApi.warning('Yüklenecek binding profili seçin');
      return;
    }

    try {
      await loadSelectedProfile(savedProfileToLoad);
      setProfileNameDraft(savedProfileToLoad);
      messageApi.success(`Binding profili yüklendi: ${savedProfileToLoad}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Binding profili yüklenemedi';
      messageApi.error(errorMessage);
    }
  };

  const handleDelete = async () => {
    if (!savedProfileToLoad) {
      return;
    }

    try {
      await deleteProfile(savedProfileToLoad);
      setSavedProfileToLoad(undefined);
      messageApi.success(`Binding profili silindi: ${savedProfileToLoad}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Binding profili silinemedi';
      messageApi.error(errorMessage);
    }
  };

  const columns: ColumnsType<BindingFieldRule> = [
    {
      title: 'JSON Yolu',
      dataIndex: 'json_path',
      key: 'json_path',
      width: 280,
      render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
    },
    {
      title: 'Şema',
      dataIndex: 'schema_type',
      key: 'schema_type',
      width: 120,
      render: (value: string) => (
        <Tag color={SCHEMA_COLORS[value] || 'default'}>
          {SCHEMA_LABELS[value] || value}
        </Tag>
      ),
    },
    {
      title: 'Önerilen',
      dataIndex: 'suggested_variable_key',
      key: 'suggested_variable_key',
      width: 180,
      render: (value: string | null, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{formatPreview(value)}</Typography.Text>
          <Typography.Text type="secondary" style={{ fontSize: 11 }}>
            {record.variable_value_preview ? formatPreview(record.variable_value_preview) : 'Önizleme yok'}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: 'Variables Anahtarı',
      dataIndex: 'variable_key',
      key: 'variable_key',
      width: 240,
      render: (value: string | null, record) => (
        <Input
          value={value || ''}
          placeholder="variables anahtarı"
          onChange={(event) =>
            updateRule(record.json_path, {
              variable_key: event.target.value || null,
            })
          }
          disabled={record.locked}
        />
      ),
    },
    {
      title: 'İşlem',
      dataIndex: 'action',
      key: 'action',
      width: 180,
      render: (value: string, record) => (
        <Select
          value={value}
          style={{ width: '100%' }}
          onChange={(nextAction) =>
            updateRule(record.json_path, {
              action: nextAction as BindingAction,
            })
          }
          disabled={record.locked}
          options={ACTION_OPTIONS}
        />
      ),
    },
    {
      title: 'Onay',
      dataIndex: 'approved',
      key: 'approved',
      width: 100,
      render: (value: boolean, record) => (
        <Checkbox
          checked={value}
          onChange={(event) =>
            updateRule(record.json_path, {
              approved: event.target.checked,
            })
          }
        />
      ),
    },
    {
      title: 'Kilit',
      dataIndex: 'locked',
      key: 'locked',
      width: 90,
      render: (value: boolean, record) => (
        <Checkbox
          checked={value}
          onChange={(event) =>
            updateRule(record.json_path, {
              locked: event.target.checked,
            })
          }
        />
      ),
    },
    {
      title: 'Kapsam',
      dataIndex: 'generator_scope',
      key: 'generator_scope',
      width: 200,
      render: (value: BindingGeneratorKey[], record) => (
        <Select
          mode="multiple"
          value={value}
          onChange={(nextValue) =>
            updateRule(record.json_path, {
              generator_scope: nextValue as BindingGeneratorKey[],
            })
          }
          style={{ width: '100%' }}
          options={[
            { value: 'bsc', label: 'BSC' },
            { value: 'ngi', label: 'NGI' },
            { value: 'ngv', label: 'NGV' },
            { value: 'opt', label: 'OPT' },
          ]}
          disabled={record.locked}
        />
      ),
    },
    {
      title: 'Güven',
      dataIndex: 'confidence',
      key: 'confidence',
      width: 100,
      render: (value: number) => <Tag color={value >= 0.8 ? 'green' : value >= 0.6 ? 'gold' : 'default'}>{Math.round(value * 100)}%</Tag>,
    },
    {
      title: 'Durum',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (value: string) => (
        <Tag color={STATUS_COLORS[value] || 'default'}>
          {STATUS_LABELS[value] || value}
        </Tag>
      ),
    },
  ];

  return (
    <Card
      title={
        <Space>
          <SettingOutlined />
          <span>Binding Studio</span>
          <Tag color="processing">{summary.total} alan</Tag>
          <Tag color="green">{summary.approved} onaylı</Tag>
          <Tag color="purple">{summary.matched} eşleşen</Tag>
          <Tag color="orange">{summary.locked} kilitli</Tag>
          <Tag color={selectedProfileName ? 'blue' : 'default'}>
            {selectedProfileName || 'kaydedilmedi'}
          </Tag>
        </Space>
      }
      extra={
        <Space wrap>
          <Button icon={<ReloadOutlined />} onClick={resetSuggestions}>
            Yeniden Eşleştir
          </Button>
        </Space>
      }
    >
      {contextHolder}
      <Space direction="vertical" style={{ width: '100%' }} size="middle">
        <Alert
          type={jsonContent ? 'info' : 'warning'}
          showIcon
          message={jsonContent ? 'JSON ve variables profili üzerinden binding önerileri hazır' : 'Binding Studio için JSON içeriği bekleniyor'}
          description={
            jsonContent
              ? `Satırları onayla, kilitle, variable key değiştir ve profile kaydet.${selectedVariableProfiles.length > 1 ? ' Backend önerileri ilk seçili variables profiline göre üretilir.' : ''}`
              : 'Bir JSON şablonu seçildiğinde binding önerileri burada görünür.'
          }
        />

        <Row gutter={[12, 12]}>
          <Col xs={24} lg={10}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Input
                value={profileNameDraft}
                onChange={(event) => setProfileNameDraft(event.target.value)}
                placeholder={buildDefaultProfileName(selectedScenarioName, jsonFile)}
                prefix={<SaveOutlined />}
              />
              <Select
                value={savedProfileToLoad}
                onChange={setSavedProfileToLoad}
                placeholder="Kaydedilmiş binding profili seç"
                options={savedProfiles.map((profile) => ({ value: profile.name, label: profile.name }))}
                allowClear
              />
            </Space>
          </Col>
          <Col xs={24} lg={14}>
            <Space wrap style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button type="primary" icon={<SaveOutlined />} onClick={handleSave} disabled={!rules.length}>
                Profili Kaydet
              </Button>
              <Button icon={<CheckSquareOutlined />} onClick={handleLoad} disabled={!savedProfileToLoad}>
                Profili Yükle
              </Button>
              <Button icon={<DeleteOutlined />} danger onClick={handleDelete} disabled={!savedProfileToLoad}>
                Sil
              </Button>
            </Space>
          </Col>
        </Row>

        <Row gutter={[12, 12]}>
          <Col xs={24} md={12}>
            <Input
              allowClear
              prefix={<SearchOutlined />}
              placeholder="JSON yolu, variables anahtarı veya şema tipi ile filtrele"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
            />
          </Col>
          <Col xs={24} md={12}>
            <Select
              allowClear
              style={{ width: '100%' }}
              placeholder="İşlem filtresi"
              value={actionFilter}
              onChange={setActionFilter}
              options={ACTION_OPTIONS}
            />
          </Col>
        </Row>

        {error ? (
          <Alert type="error" showIcon message="Binding önerileri üretilemedi" description={error} />
        ) : null}

        <Table
          rowKey="json_path"
          size="small"
          columns={columns}
          dataSource={filteredRules}
          loading={loading}
          pagination={
            filteredRules.length > 20
              ? {
                  pageSize: 20,
                  showSizeChanger: true,
                  pageSizeOptions: ['20', '50', '100'],
                  showTotal: (total, range) => `${range[0]}-${range[1]} / ${total} alan`,
                }
              : false
          }
          scroll={{ x: 1500 }}
        />
      </Space>
    </Card>
  );
};
