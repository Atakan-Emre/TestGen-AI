import React, { useEffect, useMemo, useState } from 'react';
import {
    Alert,
    App,
    Button,
    Card,
    Checkbox,
    Col,
    Descriptions,
    Divider,
    Empty,
    Input,
    Modal,
    Progress,
    Radio,
    Row,
    Select,
    Space,
    Table,
    Tag,
    Tabs,
    Statistic,
    Typography,
    message,
} from 'antd';
import type { ColumnsType } from 'antd/es/table';
import axios from 'axios';
import {
    EyeOutlined,
    CheckCircleOutlined,
    CloseCircleOutlined,
    FileTextOutlined,
    InfoCircleOutlined,
    SyncOutlined,
    SettingOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import { useScenarios } from '../../hooks/useScenarios';
import { useJsonFiles, JsonFile } from '../../hooks/useJsonFiles';
import { useTestGenerator } from '../../hooks/useTestGenerator';
import { useBindingAutoFlow } from '../../hooks/useBindingAutoFlow';
import {
    extractVariablesProfile,
    GENERATOR_DEFINITIONS,
    generatorUsesVariables,
    getGeneratorDefinition,
    summarizeGeneratorRuns,
    type GeneratedCaseSummary,
    type GeneratorRunResult,
} from '../../hooks/testGenerator.utils';
import {
    describeAutoBindingSummary,
    mapReviewReasonsToLabels,
} from '../../hooks/bindingAutoFlow.utils';
import { API_URL, IS_DEMO_MODE } from '../../config';
import type { Scenario, ScenarioMetadata } from '../../api/types';
import { BindingStudioPanel } from '../../components/BindingStudioPanel';
import type { BindingFieldRule, BindingGeneratorKey, BindingProfilePayload } from '../../types/binding';
import {
    DEMO_MODE_DESCRIPTION,
    DEMO_MODE_TITLE,
    DEMO_MUTATION_MESSAGE,
    demoScenarios,
    getDemoVariableFileContent,
} from '../../demo/demoData';

const { Option } = Select;
const { Text } = Typography;

const TYPE_COLORS: Record<string, string> = {
    bsc: 'blue',
    ngi: 'red',
    ngv: 'orange',
    opt: 'green'
};

const EXPECTED_RESULT_COLORS: Record<string, string> = {
    SUCCESS: 'green',
    VALIDATION_ERROR: 'red',
};

const mapBindingActionToBackend = (action: BindingFieldRule['action']) => {
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

const buildInlineBindingPayload = ({
    profileName,
    source,
    variablesProfile,
    rules,
}: {
    profileName: string;
    source: {
        scenario_name?: string | null;
        scenario_id?: number | string | null;
        json_file_id?: number | null;
        json_file_name?: string | null;
        variable_profiles: string[];
    };
    variablesProfile?: string;
    rules: BindingFieldRule[];
}): BindingProfilePayload => ({
    name: profileName,
    source,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    rules,
    json_file_id: source.json_file_id ?? null,
    variables_profile: variablesProfile || null,
    description: source.json_file_name
        ? `${source.json_file_name} için otomatik binding`
        : 'Otomatik binding',
    bindings: rules.map((rule) => ({
        json_path: rule.json_path,
        schema_type: rule.schema_type,
        suggested_variable_key: rule.suggested_variable_key,
        variable_key: rule.variable_key,
        confidence: Number(rule.confidence || 0),
        status: rule.approved ? 'matched' : rule.status,
        action: mapBindingActionToBackend(rule.action),
        locked: Boolean(rule.locked),
        generators: rule.generator_scope,
        approved: rule.approved,
    })),
});

const buildGeneratorInsight = (generatorKey: string, metadata: ScenarioMetadata | null) => {
    if (!metadata) {
        return 'Seçilen senaryo metadata üretmediyse generator mevcut kurallar üzerinden çalışır.';
    }

    const typeDistribution = Object.fromEntries(
        metadata.type_distribution.map((item) => [item.type, item.count])
    );

    switch (generatorKey) {
        case 'bsc':
            return `${metadata.required_count} zorunlu alan ve semantic eşleşme ile temel pozitif payload üretir.`;
        case 'ngi':
            return `${metadata.required_count} zorunlu alanı hedefler; required ve format ihlali odaklı negatif koşular üretir.`;
        case 'ngv':
            return `${typeDistribution.number || 0} numeric, ${typeDistribution.date || 0} date ve ${typeDistribution.enum || 0} enum alan üzerinden negatif değer senaryoları üretir.`;
        case 'opt':
            return `${metadata.optional_count} opsiyonel alan için kombinasyon ve boş/dolu varyasyonları üretir.`;
        default:
            return 'Generator bilgisi bulunamadı.';
    }
};

const formatBytes = (size?: number) => {
    if (!size) {
        return '0 KB';
    }

    if (size < 1024) {
        return `${size} B`;
    }

    return `${(size / 1024).toFixed(1)} KB`;
};

const buildGeneratedCaseColumns = (): ColumnsType<GeneratedCaseSummary> => [
    {
        title: 'Açıklama',
        dataIndex: 'description',
        key: 'description',
        render: (_value, record) => (
            <Space direction="vertical" size={2} style={{ width: '100%' }}>
                <Text strong>{record.description || 'Açıklama üretilmedi'}</Text>
                {record.expected_message ? (
                    <Text type="secondary">{record.expected_message}</Text>
                ) : null}
            </Space>
        )
    },
    {
        title: 'Beklenen Sonuç',
        dataIndex: 'expected_result',
        key: 'expected_result',
        width: 170,
        render: (value?: string) => (
            <Tag color={EXPECTED_RESULT_COLORS[value || ''] || 'default'}>
                {value || '-'}
            </Tag>
        )
    },
    {
        title: 'Dosya',
        dataIndex: 'file_name',
        key: 'file_name',
        width: 280,
        render: (value?: string, record?: GeneratedCaseSummary) => (
            <Text code>{value || record?.file_path?.split('/').pop() || '-'}</Text>
        )
    }
];

const TestCreatePage: React.FC = () => {
    const [messageApi, contextHolder] = message.useMessage();
    const [selectedGenerators, setSelectedGenerators] = useState<string[]>(['bsc']);
    const [selectedScenario, setSelectedScenario] = useState<string | undefined>(undefined);
    const [selectedJsons, setSelectedJsons] = useState<number[]>([]);
    const [testName, setTestName] = useState<string>('');
    const [isRunning, setIsRunning] = useState(false);
    const [terminalLogs, setTerminalLogs] = useState<string[]>([]);
    const [testResults, setTestResults] = useState<GeneratorRunResult[]>([]);
    const { scenarios, loading: scenariosLoading } = useScenarios();
    const {
        jsonFiles,
        loading: jsonFilesLoading,
        syncJsonFiles,
        selectedFile: selectedJsonDetail,
        viewJsonFile,
    } = useJsonFiles();
    const {
        variablesFiles,
        loading: variablesLoading,
        generateTestsInParallel,
        loadVariablesFiles
    } = useTestGenerator();
    const [testNames, setTestNames] = useState<{ name: string; created_at: string }[]>([]);
    const [isCustomName, setIsCustomName] = useState(true);
    const [selectedVariables, setSelectedVariables] = useState<string[]>([]);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editingFile, setEditingFile] = useState<any>(null);
    const [editContent, setEditContent] = useState('');
    const [bindingProfileName, setBindingProfileName] = useState<string | null>(null);
    const [bindingMode, setBindingMode] = useState<'auto' | 'review'>('auto');
    const { modal } = App.useApp();

    useEffect(() => {
        loadTestNames();
    }, []);

    useEffect(() => {
        if (!selectedScenario && scenarios.length > 0) {
            setSelectedScenario(String(scenarios[0].id));
        }
    }, [scenarios, selectedScenario]);

    useEffect(() => {
        const selectedJsonId = selectedJsons[0];
        if (!selectedJsonId) {
            return;
        }

        if (selectedJsonDetail?.id === selectedJsonId) {
            return;
        }

        viewJsonFile(selectedJsonId).catch(() => undefined);
    }, [selectedJsonDetail?.id, selectedJsons, viewJsonFile]);

    const loadTestNames = async () => {
        try {
            if (IS_DEMO_MODE) {
                const tests = demoScenarios.map((test) => ({
                    name: test.name,
                    created_at: test.created_at || ''
                }));
                setTestNames(tests);
                return;
            }
            const response = await axios.get(`${API_URL}/scenarios/`);
            const tests = response.data.map((test: Scenario) => ({
                name: test.name,
                created_at: test.created_at || ''
            }));
            setTestNames(tests);
        } catch (loadError) {
            console.error('Test isimleri yüklenemedi:', loadError);
        }
    };

    const selectedScenarioObj = useMemo(
        () => scenarios.find((scenario) => String(scenario.id) === String(selectedScenario)),
        [scenarios, selectedScenario]
    );

    const selectedScenarioMeta = selectedScenarioObj?.metadata || null;
    const variablesEnabled = selectedGenerators.some((generator) => generatorUsesVariables(generator));
    const selectedVariablesProfile = extractVariablesProfile(selectedVariables);
    const runSummary = useMemo(() => summarizeGeneratorRuns(testResults), [testResults]);
    const generatedCaseColumns = useMemo(() => buildGeneratedCaseColumns(), []);
    const validationIssues = useMemo(() => {
        const missing: string[] = [];
        if (!testName.trim()) missing.push('Test adı');
        if (!selectedScenario) missing.push('Senaryo');
        if (selectedJsons.length === 0) missing.push('JSON şablonu');
        if (selectedGenerators.length === 0) missing.push('Generator');
        return missing;
    }, [testName, selectedScenario, selectedJsons, selectedGenerators]);
    const selectedGeneratorDetails = useMemo(
        () => selectedGenerators.map((generatorKey) => getGeneratorDefinition(generatorKey)).filter(Boolean),
        [selectedGenerators]
    );
    const selectedJsonFile = useMemo(
        () => jsonFiles.find((file) => file.id === selectedJsons[0]) || null,
        [jsonFiles, selectedJsons]
    );
    const bindingSource = useMemo(
        () => ({
            scenario_name: selectedScenarioObj?.name || null,
            scenario_id: selectedScenarioObj?.id || null,
            json_file_id: selectedJsonFile?.id || null,
            json_file_name: selectedJsonFile?.name || null,
            variable_profiles: selectedVariablesProfile ? [selectedVariablesProfile] : [],
        }),
        [selectedJsonFile?.id, selectedJsonFile?.name, selectedScenarioObj?.id, selectedScenarioObj?.name, selectedVariablesProfile]
    );
    const {
        rules: autoBindingRules,
        loading: autoBindingLoading,
        error: autoBindingError,
        summary: autoBindingSummary,
        autoProfileName,
        canResolve: autoBindingCanResolve,
        refreshAutoProfile,
    } = useBindingAutoFlow({
        enabled: Boolean(selectedJsonFile && selectedVariablesProfile && selectedGenerators.length > 0),
        jsonContent: selectedJsonDetail?.content ?? selectedJsonFile?.content,
        selectedVariables,
        selectedGenerators: selectedGenerators as BindingGeneratorKey[],
        source: bindingSource,
    });
    const effectiveBindingProfileName = useMemo(() => {
        if (bindingMode === 'review') {
            return bindingProfileName || autoProfileName || null;
        }

        return autoProfileName || bindingProfileName || null;
    }, [autoProfileName, bindingMode, bindingProfileName]);
    const autoBindingPayload = useMemo(() => {
        if (!selectedJsonFile?.id || !selectedVariablesProfile || autoBindingRules.length === 0) {
            return null;
        }

        return buildInlineBindingPayload({
            profileName: autoProfileName || 'auto_binding_runtime',
            source: bindingSource,
            variablesProfile: selectedVariablesProfile,
            rules: autoBindingRules,
        });
    }, [
        autoBindingRules,
        autoProfileName,
        bindingSource,
        selectedJsonFile?.id,
        selectedVariablesProfile,
    ]);
    const effectiveBindingProfile = useMemo(() => {
        if (bindingMode === 'auto') {
            return autoBindingPayload || undefined;
        }

        if (bindingProfileName) {
            return bindingProfileName;
        }

        return autoBindingPayload || undefined;
    }, [autoBindingPayload, bindingMode, bindingProfileName]);
    const autoBindingReasonLabels = useMemo(
        () => mapReviewReasonsToLabels(autoBindingSummary?.review_reasons || []),
        [autoBindingSummary?.review_reasons]
    );

    const handleVariableChange = (checkedValues: any[]) => {
        setSelectedVariables(checkedValues.map((value) => String(value)));
    };

    const selectAllVariables = () => {
        if (!variablesEnabled) {
            return;
        }
        const variablesFilePaths = variablesFiles.map((file) => `variables_file:${file.name}`);
        setSelectedVariables(variablesFilePaths);
    };

    const clearAllVariables = () => {
        setSelectedVariables([]);
    };

    const handlePreviewFile = async (file: any) => {
        try {
            if (IS_DEMO_MODE) {
                const content = getDemoVariableFileContent(file.name);
                modal.info({
                    title: `Önizle: ${file.name}`,
                    content: (
                        <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '12px' }}>
                                {content}
                            </pre>
                        </div>
                    ),
                    width: 800,
                });
                return;
            }
            const response = await axios.get(`${API_URL}/files/variables/${file.name}`);
            const content = response.data.content || response.data;

            modal.info({
                title: `Önizle: ${file.name}`,
                content: (
                    <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                        <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace', fontSize: '12px' }}>
                            {content}
                        </pre>
                    </div>
                ),
                width: 800,
            });
        } catch (previewError) {
            messageApi.error('Dosya içeriği yüklenemedi');
        }
    };

    const handleEditFile = async (file: any) => {
        try {
            if (IS_DEMO_MODE) {
                setEditingFile(file);
                setEditContent(getDemoVariableFileContent(file.name));
                setEditModalVisible(true);
                return;
            }
            const response = await axios.get(`${API_URL}/files/variables/${file.name}`);
            const content = response.data.content || response.data;

            setEditingFile(file);
            setEditContent(content);
            setEditModalVisible(true);
        } catch (editError) {
            messageApi.error('Dosya içeriği yüklenemedi');
        }
    };

    const handleSaveEdit = async () => {
        if (!editingFile) {
            return;
        }

        try {
            if (IS_DEMO_MODE) {
                messageApi.info(DEMO_MUTATION_MESSAGE);
                return;
            }
            await axios.put(`${API_URL}/files/variables/${editingFile.name}`, editContent, {
                headers: {
                    'Content-Type': 'text/plain'
                }
            });

            messageApi.success('Dosya başarıyla güncellendi');
            setEditModalVisible(false);
            setEditingFile(null);
            setEditContent('');
            loadVariablesFiles();
        } catch (saveError) {
            messageApi.error('Dosya güncellenemedi');
        }
    };

    const handleGenerateToggle = (generatorKey: string) => {
        setSelectedGenerators((current) => (
            current.includes(generatorKey)
                ? current.filter((item) => item !== generatorKey)
                : [...current, generatorKey]
        ));
    };

    const handleGenerateTest = async () => {
        if (validationIssues.length > 0) {
            console.warn('Test oluşturma doğrulaması başarısız', {
                testName,
                selectedScenario,
                selectedJsons,
                selectedGenerators,
            });
            messageApi.error(`Eksik alanlar: ${validationIssues.join(', ')}`);
            return;
        }

        if (!selectedScenarioObj || !selectedScenarioObj.full_name) {
            messageApi.error('Seçilen senaryo bulunamadı');
            return;
        }

        const requestBody = {
            test_type: selectedGenerators[0],
            scenario_path: selectedScenarioObj.full_name,
            test_name: testName.trim(),
            json_file_id: selectedJsons[0],
            selected_variables: selectedVariables,
            binding_profile: effectiveBindingProfile,
        };

        setIsRunning(true);
        setTerminalLogs([]);
        setTestResults([]);

        try {
            setTerminalLogs((prev) => [
                ...prev,
                `🔄 Test oluşturuluyor: ${testName.trim()}`,
                `📝 Senaryo: ${selectedScenarioObj.name}`,
                `🧠 Generator: ${selectedScenarioMeta?.generator_type || 'metadata yok'}`,
                `🎯 Test Türleri: ${selectedGenerators.join(', ').toUpperCase()}`,
                `📊 JSON: ${selectedJsons[0]}`,
                `🧩 Variables: ${variablesEnabled ? (selectedVariablesProfile || `${selectedVariables.length} dosya`) : 'kullanılmıyor'}`,
                `🧷 Binding modu: ${bindingMode === 'auto' ? 'otomatik' : 'review'}`,
                `🧷 Aktif binding: ${effectiveBindingProfileName || (effectiveBindingProfile ? 'inline otomatik binding' : 'yok')}`,
                selectedGenerators.length > 1
                    ? '⚡ İstekler paralel başlatılıyor'
                    : '⚡ Tek generator koşusu başlatılıyor'
            ]);

            const results = await generateTestsInParallel(requestBody, selectedGenerators);
            setTestResults(results);

            const successCount = results.filter((result) => result.success).length;
            const errorCount = results.length - successCount;

            results.forEach((result) => {
                setTerminalLogs((prev) => [
                    ...prev,
                    result.success
                        ? `✅ ${result.type.toUpperCase()} tamamlandı`
                        : `❌ ${result.type.toUpperCase()} hata: ${result.message}`
                ]);
            });

            if (successCount > 0) {
                messageApi.success(`${successCount} generator başarılı${errorCount > 0 ? `, ${errorCount} generator hatalı` : ''}`);
            } else {
                messageApi.error('Hiçbir generator başarılı tamamlanmadı');
            }
        } catch (runError: any) {
            console.error('Test oluşturma hatası:', runError);
            const errorMessage = runError.response?.data?.detail || runError.message || 'Test oluşturulurken hata oluştu';
            messageApi.error(errorMessage);
            setTerminalLogs((prev) => [...prev, `❌ Hata: ${errorMessage}`]);
        } finally {
            setIsRunning(false);
        }
    };

    const jsonColumns: ColumnsType<JsonFile> = [
        {
            title: 'Dosya Adı',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => (
                <Space>
                    <FileTextOutlined />
                    <span>{text}</span>
                </Space>
            )
        },
        {
            title: 'Boyut',
            dataIndex: 'size',
            key: 'size',
            render: (size: number) => `${(size / 1024).toFixed(2)} KB`
        }
    ];

    const renderScenarioSummary = (scenario: Scenario | undefined, metadata: ScenarioMetadata | null) => {
        if (!scenario) {
            return <Empty description="Senaryo seçildiğinde özet burada görünecek" />;
        }

        return (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Descriptions size="small" column={2} bordered>
                    <Descriptions.Item label="Senaryo">{scenario.name}</Descriptions.Item>
                    <Descriptions.Item label="Generator">
                        <Tag color="blue">{metadata?.generator_type || 'manual'}</Tag>
                    </Descriptions.Item>
                    <Descriptions.Item label="Kaynak CSV">
                        {metadata?.source_csv || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Alan Sayısı">
                        {metadata?.field_count || '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Zorunlu / Opsiyonel">
                        {metadata ? `${metadata.required_count} / ${metadata.optional_count}` : '-'}
                    </Descriptions.Item>
                    <Descriptions.Item label="Tekil Alan">
                        {metadata?.unique_count || 0}
                    </Descriptions.Item>
                </Descriptions>

                {metadata ? (
                    <>
                        <div>
                            <Text strong>Semantic Tagler</Text>
                            <div style={{ marginTop: '8px' }}>
                                <Space wrap>
                                    {metadata.semantic_tags.map((tag) => (
                                        <Tag key={tag}>{tag}</Tag>
                                    ))}
                                </Space>
                            </div>
                        </div>
                        <div>
                            <Text strong>Tip Dağılımı</Text>
                            <div style={{ marginTop: '8px' }}>
                                <Space wrap>
                                    {metadata.type_distribution.map((item) => (
                                        <Tag key={`${item.type}-${item.count}`} color="processing">
                                            {item.type}: {item.count}
                                        </Tag>
                                    ))}
                                </Space>
                            </div>
                        </div>
                    </>
                ) : (
                    <Alert
                        type="info"
                        showIcon
                        message="Bu senaryo için metadata yok"
                        description="Manuel yüklenmiş veya eski formatta üretilmiş olabilir. Generatorlar fallback kurallarla çalışır."
                    />
                )}
            </Space>
        );
    };

    return (
        <App>
            {contextHolder}
            <div>
                <Card className="workspace-hero-card" style={{ marginBottom: 16 }}>
                    {IS_DEMO_MODE ? (
                        <Alert
                            type="info"
                            showIcon
                            style={{ marginBottom: 16 }}
                            message={DEMO_MODE_TITLE}
                            description={DEMO_MODE_DESCRIPTION}
                        />
                    ) : null}
                    <Row gutter={[24, 24]} align="stretch">
                        <Col xs={24} xl={16}>
                            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                <div>
                                    <Tag color="blue">Test Üretim Merkezi</Tag>
                                    <Typography.Title level={2} style={{ marginTop: 12, marginBottom: 8 }}>
                                        Test Üretim Merkezi
                                    </Typography.Title>
                                    <Typography.Paragraph className="workspace-hero-copy">
                                        Seçilen senaryo, JSON şablonu ve variables profili ile API test materyali üretimini tek akışta yönet.
                                        Çalıştırma öncesinde hazırlık durumunu, tamamlandıktan sonra sonuç özetini ve üretilen test açıklamalarını aynı ekranda gör.
                                    </Typography.Paragraph>
                                </div>
                                <Space wrap size={[8, 8]}>
                                    <Tag color="processing">{selectedGenerators.length} generator seçili</Tag>
                                    <Tag color={selectedScenarioMeta ? 'blue' : 'default'}>
                                        {selectedScenarioMeta ? `Confidence %${Math.round((selectedScenarioMeta.average_confidence || 0) * 100)}` : 'Metadata yok'}
                                    </Tag>
                                    <Tag color={selectedJsonFile ? 'green' : 'default'}>
                                        {selectedJsonFile ? selectedJsonFile.name : 'JSON seçilmedi'}
                                    </Tag>
                                    <Tag color={selectedVariablesProfile ? 'purple' : 'default'}>
                                        {selectedVariablesProfile || 'Variables profili yok'}
                                    </Tag>
                                    <Tag color={effectiveBindingProfileName ? 'cyan' : 'default'}>
                                        {effectiveBindingProfileName
                                            ? `${bindingMode === 'auto' ? 'Otomatik' : 'Review'} binding hazır`
                                            : 'Binding hazırlanmadı'}
                                    </Tag>
                                </Space>
                                <Space wrap size={[6, 6]}>
                                    {selectedGeneratorDetails.map((generator) => (
                                        <Tag key={generator?.key} color={generator?.color || 'default'}>
                                            {generator?.title}
                                        </Tag>
                                    ))}
                                </Space>
                            </Space>
                        </Col>
                        <Col xs={24} xl={8}>
                            <div className="workspace-status-panel">
                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                    <Text type="secondary">Hazırlık durumu</Text>
                                    <Progress
                                        percent={validationIssues.length === 0 ? 100 : Math.max(35, 100 - validationIssues.length * 18)}
                                        status={validationIssues.length === 0 ? 'success' : 'active'}
                                    />
                                    <Space wrap>
                                        <Tag color={validationIssues.length === 0 ? 'success' : 'warning'}>
                                            {validationIssues.length === 0 ? 'Koşu hazır' : `${validationIssues.length} eksik alan`}
                                        </Tag>
                                        <Tag color={variablesEnabled ? 'blue' : 'default'}>
                                            {variablesEnabled ? 'Variables aktif' : 'Variables pasif'}
                                        </Tag>
                                    </Space>
                                    <Typography.Text type="secondary">
                                        {selectedScenarioObj?.name || 'Henüz senaryo seçilmedi'} • {selectedJsonFile?.name || 'JSON seçilmedi'}
                                    </Typography.Text>
                                </Space>
                            </div>
                        </Col>
                    </Row>
                </Card>

                <Card title="Test Oluştur" className="test-create-card">
                    {validationIssues.length > 0 ? (
                        <Alert
                            type="warning"
                            showIcon
                            style={{ marginBottom: 16 }}
                            message="Koşu başlamadan önce tamamlanması gereken alanlar var"
                            description={`Eksik alanlar: ${validationIssues.join(', ')}`}
                        />
                    ) : (
                        <Alert
                            type="success"
                            showIcon
                            style={{ marginBottom: 16 }}
                            message="Hazır durum"
                            description="Seçilen test çalışması başlatılabilir. Generatorlar paralel çalışacaktır."
                        />
                    )}
                    <Row gutter={[16, 16]}>
                        <Col span={12}>
                            <div style={{ marginBottom: 16 }}>
                                <Space direction="vertical" style={{ width: '100%' }}>
                                    <div>Test Adı</div>
                                    {isCustomName ? (
                                        <Input
                                            placeholder="Test adı girin"
                                            value={testName}
                                            onChange={(e) => setTestName(e.target.value)}
                                            style={{ width: '100%' }}
                                        />
                                    ) : (
                                        <Select
                                            placeholder="Mevcut test seçin"
                                            style={{ width: '100%' }}
                                            onChange={(value) => setTestName(value)}
                                            value={testName}
                                        >
                                            {testNames.map((test) => (
                                                <Option key={test.name} value={test.name}>
                                                    {test.name}
                                                </Option>
                                            ))}
                                        </Select>
                                    )}
                                    <Button
                                        type="link"
                                        onClick={() => setIsCustomName(!isCustomName)}
                                        style={{ padding: 0 }}
                                    >
                                        {isCustomName ? 'Mevcut testlerden seç' : 'Yeni test adı gir'}
                                    </Button>
                                </Space>
                            </div>
                            <div style={{ marginBottom: 16 }}>
                                <Select
                                    placeholder="Senaryo Seçin"
                                    style={{ width: '100%' }}
                                    loading={scenariosLoading}
                                    value={selectedScenario}
                                    options={scenarios.map((scenario) => ({
                                        label: scenario.name,
                                        value: String(scenario.id),
                                    }))}
                                    onChange={(value) => setSelectedScenario(String(value))}
                                />
                            </div>
                            <Card
                                size="small"
                                title="Seçilen Senaryo Özeti"
                                styles={{ body: { minHeight: 220 } }}
                            >
                                {renderScenarioSummary(selectedScenarioObj, selectedScenarioMeta)}
                            </Card>
                        </Col>
                        <Col span={12}>
                            <div style={{ marginBottom: 16 }}>
                                <Space style={{ marginBottom: 16 }}>
                                    <h4>JSON Dosyası</h4>
                                    <Button
                                        icon={<SyncOutlined />}
                                        onClick={syncJsonFiles}
                                        loading={jsonFilesLoading}
                                    >
                                        Yenile
                                    </Button>
                                </Space>
                                <Alert
                                    type="info"
                                    showIcon
                                    style={{ marginBottom: '12px' }}
                                    message="Bu akışta tek JSON şablonu kullanılır"
                                    description="Tablo seçiminde yalnızca tek dosya aktif edilir; seçilen ilk JSON tüm generatorlara uygulanır."
                                />
                                <Table
                                    dataSource={jsonFiles}
                                    columns={jsonColumns}
                                    rowKey="id"
                                    rowSelection={{
                                        type: 'radio',
                                        selectedRowKeys: selectedJsons,
                                        onChange: (selectedRowKeys) => {
                                            setSelectedJsons(
                                                selectedRowKeys
                                                    .map((key) => Number(key))
                                                    .filter((key) => !Number.isNaN(key))
                                            );
                                        }
                                    }}
                                    size="small"
                                    loading={jsonFilesLoading}
                                />
                            </div>
                        </Col>
                    </Row>

                    <Divider />

                    <Row gutter={[16, 16]}>
                        <Col span={12}>
                            <Card
                                title={
                                    <Space>
                                        <SettingOutlined />
                                        <span>Variables Dosya Seçimi</span>
                                        <Tag color={variablesEnabled ? 'blue' : 'default'}>
                                            {selectedVariables.length} seçili
                                        </Tag>
                                    </Space>
                                }
                                extra={
                                    <Space>
                                        <Button size="small" onClick={selectAllVariables} disabled={!variablesEnabled}>
                                            Tümünü Seç
                                        </Button>
                                        <Button size="small" onClick={clearAllVariables}>
                                            Temizle
                                        </Button>
                                    </Space>
                                }
                            >
                                <Alert
                                    type={variablesEnabled ? 'info' : 'warning'}
                                    showIcon
                                    style={{ marginBottom: '12px' }}
                                    message={
                                        variablesEnabled
                                            ? 'Variables profili seçilen generatorlarda aktif kullanılabilir'
                                            : 'Seçili generatorlar variables kullanmıyor'
                                    }
                                    description={
                                        variablesEnabled
                                            ? 'Seçilen variables profili otomatik binding, payload üretimi ve negatif test kuralları sırasında değerlendirilir.'
                                            : 'En az bir generator seçildiğinde variables profili aktif kullanılabilir.'
                                    }
                                />

                                {variablesLoading ? (
                                    <div style={{ textAlign: 'center', padding: '20px' }}>
                                        <span>Variables dosyaları yükleniyor...</span>
                                    </div>
                                ) : variablesFiles.length === 0 ? (
                                    <div style={{ textAlign: 'center', padding: '20px', color: '#999' }}>
                                        Variables dosyası bulunamadı
                                    </div>
                                ) : (
                                    <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                                        <Checkbox.Group
                                            value={selectedVariables}
                                            onChange={handleVariableChange}
                                            style={{ width: '100%' }}
                                            disabled={!variablesEnabled}
                                        >
                                            {variablesFiles.map((file) => (
                                                <div key={file.id} style={{ marginBottom: '12px', padding: '8px', border: '1px solid #f0f0f0', borderRadius: '6px' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                                        <Checkbox value={`variables_file:${file.name}`} style={{ flex: 1 }}>
                                                            <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                                <span style={{ fontWeight: 'bold' }}>{file.name}</span>
                                                                <span style={{ fontSize: '12px', color: '#666' }}>
                                                                    {(file.size / 1024).toFixed(2)} KB - {file.type.toUpperCase()}
                                                                </span>
                                                                <Tag color="blue">
                                                                    Variables Dosyası
                                                                </Tag>
                                                            </Space>
                                                        </Checkbox>
                                                        <Space>
                                                            <Button
                                                                size="small"
                                                                icon={<EyeOutlined />}
                                                                onClick={() => handlePreviewFile(file)}
                                                            >
                                                                Önizle
                                                            </Button>
                                                            <Button
                                                                size="small"
                                                                icon={<FileTextOutlined />}
                                                                onClick={() => handleEditFile(file)}
                                                            >
                                                                Edit
                                                            </Button>
                                                        </Space>
                                                    </div>
                                                </div>
                                            ))}
                                        </Checkbox.Group>
                                    </div>
                                )}
                            </Card>
                        </Col>
                        <Col span={12}>
                            <div style={{ marginBottom: 16 }}>
                                <Space style={{ marginBottom: 16 }}>
                                    <h4>Test Türleri</h4>
                                    <Tag color="purple">{selectedGenerators.length} seçili</Tag>
                                </Space>
                                <Alert
                                    type="info"
                                    showIcon
                                    style={{ marginBottom: '12px' }}
                                    message="Birden fazla generator seçersen istekler paralel çalıştırılır"
                                    description="Aynı senaryo ve aynı JSON ile BSC, NGI, NGV ve OPT aynı koşuda üretilebilir."
                                />
                                <div className="workspace-generator-grid">
                                    {GENERATOR_DEFINITIONS.map((generator) => {
                                        const isSelected = selectedGenerators.includes(generator.key);
                                        return (
                                            <Card
                                                key={generator.key}
                                                size="small"
                                                hoverable
                                                className={isSelected ? 'workspace-generator-card selected' : 'workspace-generator-card'}
                                                onClick={() => handleGenerateToggle(generator.key)}
                                            >
                                                <Space direction="vertical" size="small" style={{ width: '100%' }}>
                                                    <Space wrap>
                                                        <Tag color={generator.color}>{generator.key.toUpperCase()}</Tag>
                                                        {isSelected ? <Tag color="success">Seçili</Tag> : <Tag>Pasif</Tag>}
                                                    </Space>
                                                    <Text strong>{generator.title}</Text>
                                                    <Text type="secondary">{generator.description}</Text>
                                                    <Text className="workspace-generator-focus">{generator.focus}</Text>
                                                    <Text style={{ fontSize: '12px' }}>
                                                        {buildGeneratorInsight(generator.key, selectedScenarioMeta)}
                                                    </Text>
                                                </Space>
                                            </Card>
                                        );
                                    })}
                                </div>
                            </div>
                        </Col>
                    </Row>

                    <div style={{ marginTop: 16 }}>
                        <Card
                            title={
                                <Space>
                                    <SettingOutlined />
                                    <span>Binding Orkestrasyonu</span>
                                    <Tag color={bindingMode === 'auto' ? 'cyan' : 'purple'}>
                                        {bindingMode === 'auto' ? 'Otomatik Mod' : 'Review Modu'}
                                    </Tag>
                                </Space>
                            }
                            extra={(
                                <Radio.Group
                                    value={bindingMode}
                                    onChange={(event) => setBindingMode(event.target.value)}
                                    optionType="button"
                                    buttonStyle="solid"
                                >
                                    <Radio.Button value="auto">Otomatik eşleştir</Radio.Button>
                                    <Radio.Button value="review">Binding Studio</Radio.Button>
                                </Radio.Group>
                            )}
                        >
                            {!selectedJsonFile ? (
                                <Alert
                                    type="info"
                                    showIcon
                                    message="Önce JSON şablonu seçin"
                                    description="Otomatik eşleştirme ve Binding Studio seçilen JSON üstünden çalışır."
                                />
                            ) : !selectedVariablesProfile ? (
                                <Alert
                                    type="info"
                                    showIcon
                                    message="Otomatik binding için variables profili seçin"
                                    description="En az bir variables dosyası seçildiğinde sistem JSON alanlarını dinamik olarak eşleştirir."
                                />
                            ) : (
                                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                                    <Alert
                                        type={
                                            autoBindingError
                                                ? 'error'
                                                : autoBindingLoading
                                                    ? 'info'
                                                    : autoBindingSummary?.review_recommended
                                                        ? 'warning'
                                                        : 'success'
                                        }
                                        showIcon
                                        message={
                                            autoBindingError
                                                ? 'Otomatik eşleştirme alınamadı'
                                                : autoBindingLoading
                                                    ? 'Otomatik eşleştirme hazırlanıyor'
                                                    : autoBindingSummary?.review_recommended
                                                        ? 'Review öneriliyor'
                                                        : 'Otomatik eşleştirme hazır'
                                        }
                                        description={
                                            autoBindingError
                                                ? autoBindingError
                                                : describeAutoBindingSummary(autoBindingSummary)
                                        }
                                    />

                                    {autoBindingCanResolve && autoBindingSummary ? (
                                        <>
                                            <Row gutter={[12, 12]}>
                                                <Col xs={24} sm={12} lg={6}>
                                                    <Card size="small">
                                                        <Statistic
                                                            title="Eşleşen Alan"
                                                            value={autoBindingSummary.matched_fields}
                                                            suffix={`/ ${autoBindingSummary.total_fields}`}
                                                        />
                                                    </Card>
                                                </Col>
                                                <Col xs={24} sm={12} lg={6}>
                                                    <Card size="small">
                                                        <Statistic
                                                            title="Öneri Alanı"
                                                            value={autoBindingSummary.suggested_fields}
                                                        />
                                                    </Card>
                                                </Col>
                                                <Col xs={24} sm={12} lg={6}>
                                                    <Card size="small">
                                                        <Statistic
                                                            title="Şablonda Korunan"
                                                            value={autoBindingSummary.template_fields}
                                                        />
                                                    </Card>
                                                </Col>
                                                <Col xs={24} sm={12} lg={6}>
                                                    <Card size="small">
                                                        <Statistic
                                                            title="Ortalama Güven"
                                                            value={Math.round(autoBindingSummary.average_confidence * 100)}
                                                            suffix="%"
                                                        />
                                                    </Card>
                                                </Col>
                                            </Row>

                                            <Descriptions size="small" bordered column={2}>
                                                <Descriptions.Item label="Aktif Profil">
                                                    {effectiveBindingProfileName || '-'}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Variables Profil">
                                                    {selectedVariablesProfile}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Match Ratio">
                                                    %{Math.round(autoBindingSummary.match_ratio * 100)}
                                                </Descriptions.Item>
                                                <Descriptions.Item label="Onaylı Alan">
                                                    {autoBindingSummary.approved_fields}
                                                </Descriptions.Item>
                                            </Descriptions>

                                            {autoBindingReasonLabels.length > 0 ? (
                                                <Space wrap>
                                                    {autoBindingReasonLabels.map((reason) => (
                                                        <Tag key={reason} color="warning">
                                                            {reason}
                                                        </Tag>
                                                    ))}
                                                </Space>
                                            ) : null}
                                        </>
                                    ) : null}

                                    <Space wrap>
                                        <Button
                                            icon={<SyncOutlined />}
                                            onClick={refreshAutoProfile}
                                            loading={autoBindingLoading}
                                            disabled={!autoBindingCanResolve}
                                        >
                                            Otomatik eşleştirmeyi yenile
                                        </Button>
                                        {bindingMode === 'auto' ? (
                                            <Button onClick={() => setBindingMode('review')}>
                                                Binding Studio ile gözden geçir
                                            </Button>
                                        ) : (
                                            <Button onClick={() => setBindingMode('auto')}>
                                                Otomatik moda dön
                                            </Button>
                                        )}
                                    </Space>

                                    {bindingMode === 'review' ? (
                                        <>
                                            <Alert
                                                type="info"
                                                showIcon
                                                message="Binding Studio opsiyonel review katmanıdır"
                                                description={
                                                    effectiveBindingProfileName
                                                        ? `Kaydedilmemiş değişiklik olsa bile üretim fallback olarak ${effectiveBindingProfileName} profilini kullanır.`
                                                        : 'Kaydettiğiniz profil üretim sırasında öncelikli kullanılır.'
                                                }
                                            />
                                            <BindingStudioPanel
                                                jsonFile={
                                                    selectedJsonFile
                                                        ? (selectedJsonDetail?.id === selectedJsonFile.id
                                                            ? selectedJsonDetail
                                                            : selectedJsonFile)
                                                        : null
                                                }
                                                selectedScenarioName={selectedScenarioObj?.name}
                                                selectedScenarioId={selectedScenarioObj?.id}
                                                selectedVariables={selectedVariables}
                                                selectedGenerators={selectedGenerators as BindingGeneratorKey[]}
                                                onBindingProfileNameChange={setBindingProfileName}
                                            />
                                        </>
                                    ) : null}
                                </Space>
                            )}
                        </Card>
                    </div>

                    <Button
                        type="primary"
                        icon={<ThunderboltOutlined />}
                        onClick={handleGenerateTest}
                        loading={isRunning}
                        style={{ marginTop: 16 }}
                        block
                    >
                        Paralel Test Oluştur
                    </Button>
                </Card>

                {testResults.length > 0 && (
                    <Row style={{ marginTop: 16 }}>
                        <Col span={24}>
                            <Card
                                title="Test Sonuçları"
                                extra={
                                    <Space>
                                        <Tag color="green">{runSummary.successCount} başarılı</Tag>
                                        <Tag color="red">{runSummary.failureCount} hatalı</Tag>
                                    </Space>
                                }
                            >
                                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                                    <Col xs={24} md={8}>
                                        <Card size="small" className="result-summary-card">
                                            <Statistic title="Toplam Koşu" value={runSummary.total} prefix={<InfoCircleOutlined />} />
                                        </Card>
                                    </Col>
                                    <Col xs={24} md={8}>
                                        <Card size="small" className="result-summary-card">
                                            <Statistic title="Başarı Oranı" value={runSummary.successRate} suffix="%" prefix={<CheckCircleOutlined />} />
                                            <Progress percent={runSummary.successRate} showInfo={false} />
                                        </Card>
                                    </Col>
                                    <Col xs={24} md={8}>
                                        <Card size="small" className="result-summary-card">
                                            <Statistic title="Hata Sayısı" value={runSummary.failureCount} prefix={<CloseCircleOutlined />} />
                                        </Card>
                                    </Col>
                                </Row>

                                <Tabs
                                    items={testResults.map((result) => ({
                                        key: result.type,
                                        label: (
                                            <Space>
                                                <Tag color={result.success ? 'success' : 'error'}>
                                                    {result.type.toUpperCase()}
                                                </Tag>
                                                <span>{result.success ? 'tamamlandı' : 'hata'}</span>
                                            </Space>
                                        ),
                                        children: (
                                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                                <Descriptions bordered size="small" column={2}>
                                                    <Descriptions.Item label="Generator">
                                                        <Tag color={TYPE_COLORS[result.type] || 'default'}>
                                                            {result.type.toUpperCase()}
                                                        </Tag>
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Durum">
                                                        <Tag color={result.success ? 'green' : 'red'}>
                                                            {result.success ? 'SUCCESS' : 'ERROR'}
                                                        </Tag>
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Mesaj" span={2}>
                                                        {result.message}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Variables Profil">
                                                        {generatorUsesVariables(result.type)
                                                            ? result.variables_profile || 'seçilmedi'
                                                            : 'kullanılmıyor'}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Scenario Confidence">
                                                        {selectedScenarioMeta
                                                            ? `%${Math.round((selectedScenarioMeta.average_confidence || 0) * 100)}`
                                                            : '-'}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Zorunlu Alan">
                                                        {selectedScenarioMeta?.required_count || 0}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Opsiyonel Alan">
                                                        {selectedScenarioMeta?.optional_count || 0}
                                                    </Descriptions.Item>
                                                    <Descriptions.Item label="Üretilen Test">
                                                        {result.generated_count}
                                                    </Descriptions.Item>
                                                </Descriptions>

                                                {result.generated_cases.length > 0 ? (
                                                    <Card
                                                        size="small"
                                                        title={`Üretilen Test Açıklamaları (${result.generated_count})`}
                                                    >
                                                        <Table
                                                            size="small"
                                                            rowKey={(record, index) => record.file_path || `${result.type}-${index}`}
                                                            columns={generatedCaseColumns}
                                                            dataSource={result.generated_cases}
                                                            pagination={
                                                                result.generated_cases.length > 8
                                                                    ? { pageSize: 8, showSizeChanger: false }
                                                                    : false
                                                            }
                                                        />
                                                    </Card>
                                                ) : null}

                                                {result.test_result?.file_path ? (
                                                    <Card size="small" title="Çıktı Dosyası">
                                                        <code className="workspace-code-block">
                                                            {result.test_result.file_path}
                                                        </code>
                                                    </Card>
                                                ) : null}

                                                {result.test_result?.test_data ? (
                                                    <Card size="small" title="Test Verisi Önizleme">
                                                        <div className="workspace-json-preview">
                                                            <pre>
                                                                {JSON.stringify(result.test_result.test_data, null, 2)}
                                                            </pre>
                                                        </div>
                                                    </Card>
                                                ) : null}
                                            </Space>
                                        )
                                    }))}
                                />
                            </Card>
                        </Col>
                    </Row>
                )}

                <Row style={{ marginTop: 16 }}>
                    <Col span={24}>
                        <Card
                            title={
                                <Space>
                                    <span>Terminal Logları</span>
                                    <Tag color={isRunning ? 'processing' : 'default'}>
                                        {isRunning ? 'Çalışıyor...' : 'Hazır'}
                                    </Tag>
                                </Space>
                            }
                            className="workspace-log-card"
                        >
                            {terminalLogs.length === 0 ? (
                                <Empty description="Henüz log bulunmuyor" />
                            ) : (
                                terminalLogs.map((log, index) => (
                                    <div
                                        key={index}
                                        className={
                                            log.includes('❌')
                                                ? 'workspace-log-entry error'
                                                : log.includes('✅')
                                                    ? 'workspace-log-entry success'
                                                    : log.includes('🔄') || log.includes('⚡')
                                                        ? 'workspace-log-entry action'
                                                        : 'workspace-log-entry'
                                        }
                                    >
                                        {log}
                                    </div>
                                ))
                            )}
                        </Card>
                    </Col>
                </Row>
            </div>

            <Modal
                title={`Edit: ${editingFile?.name || ''}`}
                open={editModalVisible}
                onOk={handleSaveEdit}
                onCancel={() => setEditModalVisible(false)}
                width={800}
                okText="Kaydet"
                cancelText="İptal"
            >
                <div style={{ marginBottom: 16 }}>
                    <label style={{ display: 'block', marginBottom: 8, fontWeight: 'bold' }}>
                        Dosya İçeriği:
                    </label>
                    <Input.TextArea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        rows={15}
                        style={{ fontFamily: 'monospace', fontSize: '12px' }}
                        placeholder="Dosya içeriğini düzenleyin..."
                    />
                </div>
            </Modal>
        </App>
    );
};

export default TestCreatePage;
