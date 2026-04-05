import React, { useState, useEffect, useRef } from 'react';
import { Steps, Button, Input, Form, Select, Card, Row, Col, Divider, App, Alert, Descriptions, Space, Tag, Progress } from 'antd';
import { UploadOutlined, FileTextOutlined, SettingOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { useCsvFiles } from '../../hooks/useCsvFiles';
import { API_URL, IS_DEMO_MODE } from '../../config';
import type { ScenarioGenerationJob, ScenarioMetadata } from '../../api/types';
import axios from 'axios';
import {
    DEMO_MODE_DESCRIPTION,
    DEMO_MODE_TITLE,
    buildDemoScenarioJob,
    demoVariableFiles,
} from '../../demo/demoData';

const { Step } = Steps;
const { Option } = Select;

interface VariableFile {
    id: number;
    name: string;
}

const JOB_STAGE_LABELS: Record<string, string> = {
    queued: 'Kuyrukta',
    starting: 'Başlatılıyor',
    validating: 'İstek doğrulanıyor',
    csv_validated: 'CSV doğrulandı',
    variables_loading: 'Variables yükleniyor',
    variables_loaded: 'Variables hazır',
    variables_skipped: 'Variables atlandı',
    variables_warning: 'Variables uyarısı',
    model_preparing: 'NLP runtime hazırlanıyor',
    embedding_model: 'Embedding modeli hazırlanıyor',
    ner_pipeline: 'NER pipeline hazırlanıyor',
    semantic_bootstrap: 'Semantic prototipler hazırlanıyor',
    csv_loading: 'CSV okunuyor',
    csv_loaded: 'CSV okundu',
    profiling: 'Alan profilleri çıkarılıyor',
    writing_output: 'Çıktı dosyaya yazılıyor',
    bundle_saved: 'Bundle kaydedildi',
    variables_applying: 'Variables uygulanıyor',
    variables_applied: 'Variables uygulandı',
    completed: 'Tamamlandı',
    failed: 'Hata',
};

const JOB_STATUS_COLORS: Record<string, string> = {
    queued: 'default',
    running: 'processing',
    completed: 'success',
    failed: 'error',
};

const ScenarioCreatePageContent: React.FC = () => {
    const [currentStep, setCurrentStep] = useState(0);
    const [selectedFile, setSelectedFile] = useState<string | null>(null);
    const [selectedFileName, setSelectedFileName] = useState<string>('');
    const [scenarioName, setScenarioName] = useState('');
    const [generatorType, setGeneratorType] = useState('nlp_hybrid');
    const { csvFiles, loading, error, fetchCsvFiles } = useCsvFiles();
    const { message } = App.useApp();
    const [generatedScenario, setGeneratedScenario] = useState<string[]>([]);
    const [generatedSummary, setGeneratedSummary] = useState<ScenarioMetadata | null>(null);
    const [generatedFile, setGeneratedFile] = useState<string>('');
    const [showResult, setShowResult] = useState(false);
    const [variablesFiles, setVariablesFiles] = useState<VariableFile[]>([]);
    const [variablesProfile, setVariablesProfile] = useState<string>('default');
    const [activeJob, setActiveJob] = useState<ScenarioGenerationJob | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const pollerRef = useRef<number | null>(null);
    const terminalStateRef = useRef<string | null>(null);

    useEffect(() => {
        fetchCsvFiles();
    }, []);

    useEffect(() => {
        const loadVariableProfiles = async () => {
            try {
                if (IS_DEMO_MODE) {
                    setVariablesFiles(demoVariableFiles.map((file) => ({ id: file.id, name: file.name })));
                    return;
                }
                const response = await axios.get(`${API_URL}/files/variables`);
                setVariablesFiles(response.data.files || []);
            } catch (loadError) {
                console.error('Variables profilleri yüklenemedi:', loadError);
            }
        };

        loadVariableProfiles();
    }, []);

    useEffect(() => {
        return () => {
            if (pollerRef.current !== null) {
                window.clearInterval(pollerRef.current);
            }
        };
    }, []);

    const stopPolling = () => {
        if (pollerRef.current !== null) {
            window.clearInterval(pollerRef.current);
            pollerRef.current = null;
        }
    };

    const applyCompletedJobResult = (job: ScenarioGenerationJob) => {
        const result = job.result;
        if (!result) {
            return;
        }
        setGeneratedScenario(result.scenarios || []);
        setGeneratedSummary(result.summary || null);
        setGeneratedFile(result.scenario_file || '');
        setShowResult(true);
    };

    const syncJobState = async (jobId: string) => {
        try {
            const response = await axios.get<ScenarioGenerationJob>(`${API_URL}/scenarios/jobs/${jobId}`);
            const job = response.data;
            setActiveJob(job);

            if (job.status === 'completed') {
                stopPolling();
                setIsGenerating(false);
                applyCompletedJobResult(job);
                const terminalKey = `${job.job_id}:${job.status}`;
                if (terminalStateRef.current !== terminalKey) {
                    terminalStateRef.current = terminalKey;
                    message.success(job.result?.message || 'Senaryo üretimi tamamlandı');
                }
            }

            if (job.status === 'failed') {
                stopPolling();
                setIsGenerating(false);
                const terminalKey = `${job.job_id}:${job.status}`;
                if (terminalStateRef.current !== terminalKey) {
                    terminalStateRef.current = terminalKey;
                    message.error(job.error || 'Senaryo üretimi başarısız oldu');
                }
            }
        } catch (jobError) {
            console.error('Senaryo job durumu alınamadı:', jobError);
        }
    };

    const startPolling = (jobId: string) => {
        stopPolling();
        void syncJobState(jobId);
        pollerRef.current = window.setInterval(() => {
            void syncJobState(jobId);
        }, 1500);
    };

    const handleNext = () => {
        if (isGenerating) {
            return;
        }
        if (currentStep === 0 && !selectedFile) {
            message.error('Lütfen bir CSV dosyası seçin');
            return;
        }
        if (currentStep === 1 && !scenarioName) {
            message.error('Lütfen senaryo adı girin');
            return;
        }
        setCurrentStep(currentStep + 1);
    };

    const handlePrev = () => {
        if (isGenerating) {
            return;
        }
        setCurrentStep(currentStep - 1);
    };

    const handleFileSelect = (value: string) => {
        setSelectedFile(value);
        const selectedCsvFile = csvFiles?.find(file => file.id.toString() === value);
        if (selectedCsvFile) {
            setSelectedFileName(selectedCsvFile.name);
        }
    };

    const handleGenerateScenarios = async () => {
        try {
            if (!selectedFile || !scenarioName) {
                message.error('Lütfen tüm alanları doldurun');
                return;
            }

            if (IS_DEMO_MODE) {
                const demoJob = buildDemoScenarioJob(scenarioName, selectedFileName || 'example.csv');
                setGeneratedScenario([]);
                setGeneratedSummary(null);
                setGeneratedFile('');
                setShowResult(false);
                setIsGenerating(true);
                setActiveJob({
                    ...demoJob,
                    status: 'running',
                    progress: 0.35,
                    current_stage: 'semantic_bootstrap',
                });

                window.setTimeout(() => {
                    setActiveJob(demoJob);
                    applyCompletedJobResult(demoJob);
                    setIsGenerating(false);
                    message.success('Demo senaryo bundle hazır');
                }, 700);
                return;
            }

            const requestData = {
                name: scenarioName,
                csv_file_id: parseInt(selectedFile),
                csv_file_name: selectedFileName,
                generator_type: generatorType,
                variables_profile: variablesProfile
            };

            setGeneratedScenario([]);
            setGeneratedSummary(null);
            setGeneratedFile('');
            setShowResult(false);
            setIsGenerating(true);
            terminalStateRef.current = null;

            const response = await axios.post<ScenarioGenerationJob>(`${API_URL}/scenarios/jobs`, requestData);
            setActiveJob(response.data);
            message.info('Senaryo üretimi başlatıldı. Durum panelinden canlı izleyebilirsiniz.');
            startPolling(response.data.job_id);

        } catch (error) {
            console.error('Senaryo oluşturma hatası:', error);
            setIsGenerating(false);
            message.error('Test senaryoları oluşturulurken bir hata oluştu');
        }
    };

    const handleGoToList = () => {
        const basePath = import.meta.env.BASE_URL || '/';
        const normalizedBase = basePath.endsWith('/') ? basePath : `${basePath}/`;
        window.location.href = `${normalizedBase}scenarios/list`;
    };

    const steps = [
        {
            title: 'CSV Seç',
            icon: <FileTextOutlined />,
            content: (
                <Card 
                    title="CSV Dosyası Seçimi" 
                    bordered={false}
                    className="step-card"
                    style={{ width: '100%', maxWidth: '800px' }}
                >
                    <Form.Item 
                        label="CSV Dosyası" 
                        required 
                        help="Test senaryoları oluşturmak için bir CSV dosyası seçin"
                    >
                        <Select
                            placeholder="CSV dosyası seçin"
                            onChange={handleFileSelect}
                            loading={loading}
                            style={{ width: '100%' }}
                            size="large"
                            value={selectedFile}
                        >
                            {csvFiles?.map((file: any) => (
                                <Option key={file.id} value={file.id.toString()} label={file.name}>
                                    <FileTextOutlined /> {file.name}
                                </Option>
                            ))}
                        </Select>
                    </Form.Item>
                </Card>
            ),
        },
        {
            title: 'Senaryo Bilgileri',
            icon: <SettingOutlined />,
            content: (
                <Card 
                    title="Senaryo Yapılandırması" 
                    bordered={false}
                    className="step-card"
                    style={{ width: '100%', maxWidth: '800px' }}
                >
                    <Row gutter={[24, 24]}>
                        <Col span={24}>
                            <Form.Item 
                                label="Senaryo Adı" 
                                required
                                help="Oluşturulacak senaryo için benzersiz bir isim girin"
                            >
                                <Input
                                    placeholder="Senaryo adini girin"
                                    value={scenarioName}
                                    onChange={(e) => setScenarioName(e.target.value)}
                                    size="large"
                                    prefix={<FileTextOutlined />}
                                />
                            </Form.Item>
                        </Col>
                        <Col span={24}>
                            <Form.Item 
                                label="Generator Tipi"
                                help="Senaryo oluşturma yöntemini seçin"
                            >
                                <Select
                                    value={generatorType}
                                    onChange={(value) => setGeneratorType(value)}
                                    style={{ width: '100%' }}
                                    size="large"
                                >
                                    <Option value="nlp_hybrid">NLP Hybrid Generator</Option>
                                    <Option value="bert_ner">BERT NER Compatible</Option>
                                    <Option value="rule_based">Rule Based Generator</Option>
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={24}>
                            <Form.Item
                                label="Variables Profili"
                                help="İsterseniz senaryo placeholder alanlarını bir environment profili ile önceden zenginleştirin"
                            >
                                <Select
                                    value={variablesProfile}
                                    onChange={(value) => setVariablesProfile(value)}
                                    style={{ width: '100%' }}
                                    size="large"
                                >
                                    <Option value="default">Varsayılan / Boş Profil</Option>
                                    {variablesFiles.map((file) => (
                                        <Option
                                            key={file.id}
                                            value={file.name.replace(/\.[^.]+$/, '')}
                                        >
                                            {file.name}
                                        </Option>
                                    ))}
                                </Select>
                            </Form.Item>
                        </Col>
                        <Col span={24}>
                            <Alert
                                type="info"
                                showIcon
                                message="Önerilen akış"
                                description={
                                    generatorType === 'nlp_hybrid'
                                        ? 'CSV yapısı rule-based okunur, alan tipleri ve semantic tagler embedding/NER ile zenginleştirilir, sonuç .txt ve .meta.json bundle olarak kaydedilir.'
                                        : generatorType === 'rule_based'
                                            ? 'Sadece yapısal CSV kuralları kullanılır. Daha hızlıdır ama semantic zenginlik düşer.'
                                            : 'BERT NER uyumlu mod geriye dönük isim korur; aktif altyapı yine hibrit bundle üretimidir.'
                                }
                            />
                        </Col>
                    </Row>
                </Card>
            ),
        },
        {
            title: 'Onay',
            icon: <CheckCircleOutlined />,
            content: (
                <div style={{ width: '100%', maxWidth: '1000px' }}>
                    <Card 
                        title="Seçilen Bilgilerin Özeti" 
                        bordered={false}
                        className="step-card"
                    >
                        <Row gutter={[16, 16]}>
                            <Col span={24}>
                                <Card type="inner" title="CSV Dosyası">
                                    <p><FileTextOutlined /> {selectedFileName}</p>
                                </Card>
                            </Col>
                            <Col span={24}>
                                <Card type="inner" title="Senaryo Adı">
                                    <p>{scenarioName}</p>
                                </Card>
                            </Col>
                            <Col span={24}>
                                <Card type="inner" title="Generator Tipi">
                                    <p>{generatorType}</p>
                                </Card>
                            </Col>
                            <Col span={24}>
                                <Card type="inner" title="Variables Profili">
                                    <p>{variablesProfile === 'default' ? 'Varsayılan / Boş Profil' : variablesProfile}</p>
                                </Card>
                            </Col>
                        </Row>
                    </Card>

                    {showResult && generatedScenario.length > 0 && (
                        <Card 
                            title="Oluşturulan Test Senaryoları" 
                            style={{ marginTop: '24px' }}
                            extra={
                                <Button 
                                    type="primary" 
                                    icon={<FileTextOutlined />}
                                    onClick={handleGoToList}
                                >
                                    Senaryo Listesine Git
                                </Button>
                            }
                        >
                            {generatedSummary && (
                                <Card
                                    type="inner"
                                    title={
                                        <Space>
                                            <span>NLP Bundle Özeti</span>
                                            <Tag color="blue">{generatedSummary.generator_type}</Tag>
                                        </Space>
                                    }
                                    style={{ marginBottom: '16px' }}
                                >
                                    <Descriptions column={2} size="small">
                                        <Descriptions.Item label="Senaryo Dosyası">
                                            {generatedFile || '-'}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Kaynak CSV">
                                            {generatedSummary.source_csv}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Alan Sayısı">
                                            {generatedSummary.field_count}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Ortalama Güven">
                                            %{Math.round((generatedSummary.average_confidence || 0) * 100)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Zorunlu / Opsiyonel">
                                            {generatedSummary.required_count} / {generatedSummary.optional_count}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Tekil Alan">
                                            {generatedSummary.unique_count}
                                        </Descriptions.Item>
                                    </Descriptions>
                                    <div style={{ marginTop: '12px' }}>
                                        <Space wrap>
                                            {generatedSummary.semantic_tags.map((tag) => (
                                                <Tag key={tag}>{tag}</Tag>
                                            ))}
                                        </Space>
                                    </div>
                                </Card>
                            )}
                            <div style={{ 
                                maxHeight: '400px', 
                                overflowY: 'auto',
                                padding: '16px',
                                backgroundColor: '#f5f5f5',
                                borderRadius: '4px'
                            }}>
                                {generatedScenario.map((senaryo, index) => (
                                    <p key={index} style={{ margin: '8px 0', fontSize: '14px', lineHeight: '1.6' }}>
                                        {index + 1}. {senaryo}
                                    </p>
                                ))}
                            </div>
                        </Card>
                    )}

                    {activeJob && (
                        <Card
                            title="Üretim Durumu"
                            style={{ marginTop: '24px' }}
                            extra={
                                <Tag color={JOB_STATUS_COLORS[activeJob.status] || 'default'}>
                                    {activeJob.status === 'running'
                                        ? 'Çalışıyor'
                                        : activeJob.status === 'completed'
                                            ? 'Tamamlandı'
                                            : activeJob.status === 'failed'
                                                ? 'Hata'
                                                : 'Kuyrukta'}
                                </Tag>
                            }
                        >
                            <Space direction="vertical" style={{ width: '100%' }} size="middle">
                                <Progress
                                    percent={Math.round((activeJob.progress || 0) * 100)}
                                    status={
                                        activeJob.status === 'failed'
                                            ? 'exception'
                                            : activeJob.status === 'completed'
                                                ? 'success'
                                                : 'active'
                                    }
                                />
                                <Descriptions size="small" column={2}>
                                    <Descriptions.Item label="İş Kimliği">
                                        {activeJob.job_id}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Aşama">
                                        {JOB_STAGE_LABELS[activeJob.current_stage] || activeJob.current_stage}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Oluşturuldu">
                                        {new Date(activeJob.created_at).toLocaleString('tr-TR')}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Son Güncelleme">
                                        {new Date(activeJob.updated_at).toLocaleString('tr-TR')}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Durum">
                                        {activeJob.status}
                                    </Descriptions.Item>
                                    <Descriptions.Item label="Çıktı Dosyası">
                                        {activeJob.result?.scenario_file || generatedFile || '-'}
                                    </Descriptions.Item>
                                </Descriptions>

                                {activeJob.error && (
                                    <Alert
                                        type="error"
                                        showIcon
                                        message="Senaryo üretimi başarısız"
                                        description={activeJob.error}
                                    />
                                )}

                                <Card type="inner" title="Canlı Log">
                                    <div
                                        style={{
                                            maxHeight: '280px',
                                            overflowY: 'auto',
                                            padding: '12px',
                                            background: '#0f172a',
                                            color: '#e2e8f0',
                                            borderRadius: '8px',
                                            fontFamily: 'Menlo, Monaco, Consolas, monospace',
                                            fontSize: '12px',
                                            lineHeight: 1.7,
                                        }}
                                    >
                                        {activeJob.logs.length > 0 ? (
                                            activeJob.logs.map((entry) => (
                                                <div key={`${entry.timestamp}-${entry.message}`}>
                                                    <span style={{ color: '#94a3b8' }}>
                                                        [{new Date(entry.timestamp).toLocaleTimeString('tr-TR')}]
                                                    </span>{' '}
                                                    <span
                                                        style={{
                                                            color: entry.level === 'error'
                                                                ? '#fca5a5'
                                                                : entry.level === 'warning'
                                                                    ? '#fcd34d'
                                                                    : '#93c5fd',
                                                        }}
                                                    >
                                                        {entry.level.toUpperCase()}
                                                    </span>{' '}
                                                    <span>{entry.message}</span>
                                                </div>
                                            ))
                                        ) : (
                                            <div>Log bekleniyor...</div>
                                        )}
                                    </div>
                                </Card>
                            </Space>
                        </Card>
                    )}
                </div>
            ),
        },
    ];

    return (
            <div style={{ padding: '32px', maxWidth: '1400px', margin: '0 auto' }}>
            <Card>
                {IS_DEMO_MODE ? (
                    <Alert
                        type="info"
                        showIcon
                        style={{ marginBottom: 24 }}
                        message={DEMO_MODE_TITLE}
                        description={DEMO_MODE_DESCRIPTION}
                    />
                ) : null}
                <h1 style={{ fontSize: '28px', marginBottom: '32px', textAlign: 'center' }}>
                    Test Senaryosu Oluştur
                </h1>
                
                <Steps 
                    current={currentStep} 
                    style={{ marginBottom: '40px', padding: '0 32px' }}
                    progressDot
                >
                    {steps.map(item => (
                        <Step 
                            key={item.title} 
                            title={item.title} 
                            icon={item.icon}
                        />
                    ))}
                </Steps>

                <div style={{ 
                    marginTop: '32px', 
                    marginBottom: '32px',
                    minHeight: '400px',
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'flex-start'
                }}>
                    {steps[currentStep].content}
                </div>

                <Divider />

                <div style={{ 
                    marginTop: '24px',
                    display: 'flex',
                    justifyContent: 'center',
                    gap: '16px'
                }}>
                    {currentStep > 0 && (
                        <Button 
                            size="large"
                            onClick={handlePrev}
                            disabled={isGenerating}
                        >
                            Geri
                        </Button>
                    )}
                    {currentStep < steps.length - 1 && (
                        <Button 
                            type="primary" 
                            size="large"
                            onClick={handleNext}
                            disabled={isGenerating}
                        >
                            İleri
                        </Button>
                    )}
                    {currentStep === steps.length - 1 && (
                        <Button 
                            type="primary" 
                            size="large"
                            onClick={handleGenerateScenarios}
                            icon={<CheckCircleOutlined />}
                            loading={isGenerating}
                            disabled={isGenerating}
                        >
                            {isGenerating ? 'Üretim Devam Ediyor' : 'Senaryoları Oluştur'}
                        </Button>
                    )}
                </div>
            </Card>
        </div>
    );
};

export const ScenarioCreatePage: React.FC = () => {
    return (
        <App>
            <ScenarioCreatePageContent />
        </App>
    );
}; 
