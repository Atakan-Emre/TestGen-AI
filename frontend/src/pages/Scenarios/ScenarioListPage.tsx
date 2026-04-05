import React, { useMemo, useState } from 'react';
import {
    Alert,
    App,
    Button,
    Descriptions,
    Modal,
    Space,
    Table,
    Tabs,
    Tag,
    Typography,
    Upload,
} from 'antd';
import { DeleteOutlined, EyeOutlined, UploadOutlined, SyncOutlined, FileTextOutlined, PlusOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { useScenarios } from '../../hooks/useScenarios';
import type { Scenario, ScenarioFieldMetadata, ScenarioMetadata } from '../../api/types';

const { Title, Text } = Typography;

interface ScenarioDetailState {
    content: string;
    metadata: ScenarioMetadata | null;
}

export const ScenarioListPage: React.FC = () => {
    const {
        scenarios,
        loading: isLoading,
        deleteScenario,
        uploadScenario,
        syncScenarios,
        getScenarioDetail,
        error
    } = useScenarios();

    const [selectedScenario, setSelectedScenario] = useState<Scenario | null>(null);
    const [isViewModalVisible, setIsViewModalVisible] = useState(false);
    const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
    const [scenarioDetail, setScenarioDetail] = useState<ScenarioDetailState>({ content: '', metadata: null });
    const { message } = App.useApp();

    const fieldColumns = [
        {
            title: 'Alan',
            dataIndex: 'field_name_tr',
            key: 'field_name_tr',
            render: (_text: string, record: ScenarioFieldMetadata) => (
                <div>
                    <Text strong>{record.field_name_tr}</Text>
                    <div style={{ color: '#666', fontSize: '12px' }}>{record.field_name_en}</div>
                </div>
            )
        },
        {
            title: 'Tip',
            dataIndex: 'field_type',
            key: 'field_type',
            width: 120,
            render: (value: string) => <Tag>{value || 'unknown'}</Tag>,
        },
        {
            title: 'Kurallar',
            key: 'rules',
            render: (_text: string, record: ScenarioFieldMetadata) => (
                <Space size={[4, 8]} wrap>
                    {record.required && <Tag color="red">required</Tag>}
                    {record.optional && <Tag color="green">optional</Tag>}
                    {record.unique && <Tag color="gold">unique</Tag>}
                    {record.max_len ? <Tag>max {record.max_len}</Tag> : null}
                </Space>
            )
        },
        {
            title: 'Güven',
            dataIndex: 'confidence',
            key: 'confidence',
            width: 110,
            render: (value: number) => `%${Math.round((value || 0) * 100)}`
        }
    ];

    const columns = [
        {
            title: 'Senaryo Adı',
            dataIndex: 'name',
            key: 'name',
            render: (text: string, record: Scenario) => (
                <Space direction="vertical" size={2}>
                    <Space>
                        <FileTextOutlined style={{ color: '#1890ff' }} />
                        <Text strong>{text}</Text>
                    </Space>
                    <Text type="secondary">{record.filename}</Text>
                </Space>
            )
        },
        {
            title: 'Generator',
            key: 'generator',
            width: 160,
            render: (_text: string, record: Scenario) => (
                <Tag color="blue">{record.metadata?.generator_type || 'manual'}</Tag>
            )
        },
        {
            title: 'Kaynak CSV',
            key: 'source_csv',
            render: (_text: string, record: Scenario) => record.metadata?.source_csv || '-'
        },
        {
            title: 'Alan',
            key: 'field_count',
            width: 90,
            render: (_text: string, record: Scenario) => record.metadata?.field_count || '-'
        },
        {
            title: 'Confidence',
            key: 'confidence',
            width: 120,
            render: (_text: string, record: Scenario) => (
                record.metadata
                    ? `%${Math.round((record.metadata.average_confidence || 0) * 100)}`
                    : '-'
            )
        },
        {
            title: 'Güncelleme',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 180,
            render: (value: string) => value ? new Date(value).toLocaleString('tr-TR') : '-'
        },
        {
            title: 'İşlemler',
            key: 'actions',
            render: (_: any, record: Scenario) => (
                <Space>
                    <Button
                        type="primary"
                        icon={<EyeOutlined />}
                        onClick={() => handleView(record)}
                    >
                        Görüntüle
                    </Button>
                    <Button
                        danger
                        type="primary"
                        icon={<DeleteOutlined />}
                        onClick={() => handleDelete(record)}
                    >
                        Sil
                    </Button>
                </Space>
            ),
        },
    ];

    const topDistribution = useMemo(
        () => scenarioDetail.metadata?.type_distribution || [],
        [scenarioDetail.metadata]
    );

    const handleUpload = async (file: File) => {
        try {
            await uploadScenario(file);
            message.success('Senaryo başarıyla yüklendi');
        } catch (uploadError) {
            message.error('Senaryo yüklenirken bir hata oluştu');
        }
    };

    const handleDelete = (scenario: Scenario) => {
        setSelectedScenario(scenario);
        setIsDeleteModalVisible(true);
    };

    const handleSync = async () => {
        try {
            await syncScenarios();
            message.success('Senaryolar başarıyla senkronize edildi');
        } catch (syncError) {
            message.error('Senaryolar senkronize edilirken bir hata oluştu');
        }
    };

    const handleView = async (scenario: Scenario) => {
        try {
            setSelectedScenario(scenario);
            const detail = await getScenarioDetail(scenario.filename || `${scenario.name}.txt`);
            setScenarioDetail({
                content: detail.content,
                metadata: detail.metadata || null,
            });
            setIsViewModalVisible(true);
        } catch (viewError) {
            message.error('Senaryo içeriği alınırken bir hata oluştu');
        }
    };

    const confirmDelete = async () => {
        if (selectedScenario) {
            try {
                await deleteScenario(selectedScenario.id);
                message.success('Senaryo başarıyla silindi');
                setIsDeleteModalVisible(false);
            } catch (deleteError) {
                console.error('Silme hatası:', deleteError);
                message.error('Senaryo silinirken hata oluştu');
            }
        }
    };

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
                <div>
                    <Title level={2} style={{ marginBottom: 0 }}>
                        <FileTextOutlined /> Test Senaryoları
                    </Title>
                    <Text type="secondary">
                        NLP bundle metadata ile üretilen veya yüklenen senaryoların merkezi listesi.
                    </Text>
                </div>
                <Space wrap>
                    <Link to="/scenarios/create">
                        <Button type="primary" icon={<PlusOutlined />}>
                            Yeni Senaryo Oluştur
                        </Button>
                    </Link>
                    <Upload
                        accept=".txt"
                        showUploadList={false}
                        beforeUpload={(file) => {
                            handleUpload(file);
                            return false;
                        }}
                    >
                        <Button icon={<UploadOutlined />}>
                            Senaryo Yükle
                        </Button>
                    </Upload>
                    <Button
                        icon={<SyncOutlined />}
                        onClick={handleSync}
                    >
                        Senkronize Et
                    </Button>
                </Space>
            </div>

            {error ? (
                <Alert
                    type="warning"
                    showIcon
                    style={{ marginBottom: '16px' }}
                    message="Senaryo verisi alınırken uyarı oluştu"
                    description={error}
                />
            ) : null}

            <Table
                columns={columns}
                dataSource={scenarios}
                loading={isLoading}
                rowKey="id"
            />

            <Modal
                title={
                    <Space>
                        <FileTextOutlined />
                        {selectedScenario?.name || ''} Detayı
                    </Space>
                }
                open={isViewModalVisible}
                onCancel={() => setIsViewModalVisible(false)}
                width={960}
                footer={null}
            >
                <Tabs
                    items={[
                        {
                            key: 'content',
                            label: 'Senaryo Metni',
                            children: (
                                <pre style={{
                                    maxHeight: '500px',
                                    overflow: 'auto',
                                    whiteSpace: 'pre-wrap',
                                    wordWrap: 'break-word',
                                    backgroundColor: '#f5f5f5',
                                    padding: '12px',
                                    borderRadius: '4px'
                                }}>
                                    {scenarioDetail.content}
                                </pre>
                            )
                        },
                        {
                            key: 'metadata',
                            label: 'NLP Özeti',
                            children: scenarioDetail.metadata ? (
                                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                                    <Descriptions bordered size="small" column={2}>
                                        <Descriptions.Item label="Generator">
                                            <Tag color="blue">{scenarioDetail.metadata.generator_type}</Tag>
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Kaynak CSV">
                                            {scenarioDetail.metadata.source_csv}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Alan Sayısı">
                                            {scenarioDetail.metadata.field_count}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Ortalama Güven">
                                            %{Math.round((scenarioDetail.metadata.average_confidence || 0) * 100)}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Zorunlu / Opsiyonel">
                                            {scenarioDetail.metadata.required_count} / {scenarioDetail.metadata.optional_count}
                                        </Descriptions.Item>
                                        <Descriptions.Item label="Tekil Alan">
                                            {scenarioDetail.metadata.unique_count}
                                        </Descriptions.Item>
                                    </Descriptions>

                                    <div>
                                        <Text strong>Semantic Tagler</Text>
                                        <div style={{ marginTop: '8px' }}>
                                            <Space wrap>
                                                {scenarioDetail.metadata.semantic_tags.map((tag) => (
                                                    <Tag key={tag}>{tag}</Tag>
                                                ))}
                                            </Space>
                                        </div>
                                    </div>

                                    <div>
                                        <Text strong>Tip Dağılımı</Text>
                                        <div style={{ marginTop: '8px' }}>
                                            <Space wrap>
                                                {topDistribution.map((item) => (
                                                    <Tag key={`${item.type}-${item.count}`} color="processing">
                                                        {item.type}: {item.count}
                                                    </Tag>
                                                ))}
                                            </Space>
                                        </div>
                                    </div>

                                    <Table
                                        columns={fieldColumns}
                                        dataSource={scenarioDetail.metadata.fields || []}
                                        rowKey={(record: ScenarioFieldMetadata) => `${record.field_name_en}-${record.field_name_tr}`}
                                        size="small"
                                        pagination={{ pageSize: 8 }}
                                    />
                                </Space>
                            ) : (
                                <Alert
                                    type="info"
                                    showIcon
                                    message="Metadata bulunamadı"
                                    description="Bu senaryo manuel yüklenmiş olabilir veya .meta.json sidecar dosyası bulunmuyor olabilir."
                                />
                            )
                        }
                    ]}
                />
            </Modal>

            <Modal
                title={
                    <Space>
                        <DeleteOutlined style={{ color: '#ff4d4f' }} />
                        Senaryo Silme
                    </Space>
                }
                open={isDeleteModalVisible}
                onOk={confirmDelete}
                onCancel={() => setIsDeleteModalVisible(false)}
                okText="Sil"
                cancelText="İptal"
                okButtonProps={{ danger: true }}
            >
                <Space>
                    <DeleteOutlined style={{ color: '#ff4d4f', fontSize: '24px' }} />
                    <p>
                        <strong>{selectedScenario?.name}</strong> senaryosunu silmek istediğinizden emin misiniz?
                        <br />
                        Bu işlem geri alınamaz.
                    </p>
                </Space>
            </Modal>
        </div>
    );
};
