import React, { useEffect, useMemo, useState } from 'react';
import {
    Alert,
    App,
    Button,
    Card,
    Col,
    Empty,
    Progress,
    Row,
    Skeleton,
    Space,
    Statistic,
    Table,
    Tag,
    Typography,
} from 'antd';
import {
    ApiOutlined,
    DashboardOutlined,
    DatabaseOutlined,
    ExperimentOutlined,
    FileTextOutlined,
    FolderOpenOutlined,
    ReloadOutlined,
    ThunderboltOutlined,
} from '@ant-design/icons';
import type { TableProps } from 'antd';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { API_URL } from '../../config';

const { Title, Text } = Typography;

interface DashboardTypeSummary {
    key: 'bsc' | 'ngv' | 'ngi' | 'opt';
    label: string;
    suite_count: number;
    case_count: number;
}

interface DashboardInputSummary {
    key: string;
    label: string;
    count: number;
}

interface DashboardScenario {
    id: string;
    name: string;
    date: string;
    filename: string;
    updated_at: string;
    size: number;
}

interface DashboardTestType {
    key: 'bsc' | 'ngv' | 'ngi' | 'opt';
    label: string;
    count: number;
}

interface DashboardTestSuite {
    name: string;
    created_at: string;
    updated_at: string;
    total_files: number;
    types: DashboardTestType[];
}

interface DashboardSummary {
    status: string;
    generated_at: string;
    counts: {
        csv_files: number;
        json_files: number;
        variable_files: number;
        input_files: number;
        scenarios: number;
        test_suites: number;
        test_cases: number;
    };
    input_breakdown: DashboardInputSummary[];
    test_types: DashboardTypeSummary[];
    recent_scenarios: DashboardScenario[];
    recent_tests: DashboardTestSuite[];
}

const TYPE_COLORS: Record<DashboardTypeSummary['key'], string> = {
    bsc: 'blue',
    ngv: 'green',
    ngi: 'red',
    opt: 'orange',
};

export const HomePage: React.FC = () => {
    const { message } = App.useApp();
    const [dashboard, setDashboard] = useState<DashboardSummary | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchDashboard = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await axios.get<DashboardSummary>(`${API_URL}/dashboard/summary`);
            setDashboard(response.data);
        } catch (err) {
            console.error('Dashboard yüklenirken hata:', err);
            setError('Dashboard verileri yüklenemedi');
            message.error('Dashboard verileri yüklenemedi');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchDashboard();
    }, []);

    const totalCases = dashboard?.counts.test_cases || 0;
    const topGenerator = dashboard?.test_types.reduce<DashboardTypeSummary | null>((top, current) => {
        if (!top || current.case_count > top.case_count) {
            return current;
        }
        return top;
    }, null);
    const latestScenario = dashboard?.recent_scenarios?.[0] || null;
    const latestTestSuite = dashboard?.recent_tests?.[0] || null;
    const totalInputs = useMemo(
        () => (dashboard ? dashboard.counts.csv_files + dashboard.counts.json_files + dashboard.counts.variable_files : 0),
        [dashboard]
    );
    const healthLabel = dashboard?.status === 'healthy' ? 'Sistem hazır' : 'Veri bekleniyor';

    const scenarioColumns: TableProps<DashboardScenario>['columns'] = [
        {
            title: 'Senaryo',
            dataIndex: 'name',
            key: 'name',
            render: (_value: string, record: DashboardScenario) => (
                <div>
                    <Text strong>{record.name}</Text>
                    <div className="home-table-subtitle">{record.filename}</div>
                </div>
            ),
        },
        {
            title: 'Güncelleme',
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (value: string) => new Date(value).toLocaleString('tr-TR'),
        },
        {
            title: 'Boyut',
            dataIndex: 'size',
            key: 'size',
            width: 110,
            render: (value: number) => `${Math.max(1, Math.round(value / 1024))} KB`,
        },
    ];

    const testColumns: TableProps<DashboardTestSuite>['columns'] = [
        {
            title: 'Test Paketi',
            dataIndex: 'name',
            key: 'name',
            render: (_value: string, record: DashboardTestSuite) => (
                <div>
                    <Text strong>{record.name}</Text>
                    <div className="home-table-subtitle">{record.total_files} dosya</div>
                </div>
            ),
        },
        {
            title: 'Tipler',
            dataIndex: 'types',
            key: 'types',
            render: (types: DashboardTestType[]) => (
                <Space size={[4, 8]} wrap>
                    {types.length > 0 ? (
                        types.map((type) => (
                            <Tag key={`${type.key}-${type.count}`} color={TYPE_COLORS[type.key]}>
                                {type.label}: {type.count}
                            </Tag>
                        ))
                    ) : (
                        <Tag>Henüz çıktı yok</Tag>
                    )}
                </Space>
            ),
        },
        {
            title: 'Güncelleme',
            dataIndex: 'updated_at',
            key: 'updated_at',
            width: 180,
            render: (value: string) => new Date(value).toLocaleString('tr-TR'),
        },
    ];

    return (
        <div className="home-container">
            <div className="home-hero">
                <div className="home-hero-copy">
                    <div className="home-header">
                        <Title level={2}>
                            <DashboardOutlined /> TestGen AI Gösterge Paneli
                        </Title>
                    </div>
                    <Text className="home-hero-text">
                        TestGen AI için girdi dosyaları, üretilen senaryolar ve test çıktılarını tek ekranda izleyin.
                    </Text>
                    <div className="home-hero-meta">
                        <Tag color={dashboard?.status === 'healthy' ? 'success' : 'default'}>
                            API: {dashboard?.status === 'healthy' ? 'Hazır' : 'Bilinmiyor'}
                        </Tag>
                        <Tag color="processing">{healthLabel}</Tag>
                        <span>
                            Son yenileme: {dashboard ? new Date(dashboard.generated_at).toLocaleString('tr-TR') : '-'}
                        </span>
                    </div>
                    <div className="home-hero-meta">
                        <Tag color="blue">{dashboard?.counts.scenarios || 0} senaryo</Tag>
                        <Tag color="cyan">{dashboard?.counts.test_suites || 0} paket</Tag>
                        <Tag color="green">{dashboard?.counts.test_cases || 0} case</Tag>
                        <Tag color="orange">{totalInputs} kaynak</Tag>
                    </div>
                </div>
                <Card className="home-hero-panel">
                    <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                        <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                            <Text strong>Canlı durum kartı</Text>
                            <Tag color={dashboard?.status === 'healthy' ? 'success' : 'default'}>
                                {dashboard?.status === 'healthy' ? 'Aktif' : 'Beklemede'}
                            </Tag>
                        </Space>
                        <div className="home-hero-mini-grid">
                            <Statistic title="Toplam Case" value={totalCases} />
                            <Statistic title="En yoğun generator" value={topGenerator?.key?.toUpperCase() || '-'} />
                            <Statistic title="Son test paketi" value={latestTestSuite?.name || '-'} />
                        </div>
                        <div className="home-hero-actions">
                            <Button icon={<ReloadOutlined />} onClick={fetchDashboard} loading={loading} block>
                                Yenile
                            </Button>
                        </div>
                        <Text type="secondary">
                            {latestScenario ? `Son senaryo: ${latestScenario.name}` : 'Henüz üretilmiş senaryo yok'}
                        </Text>
                    </Space>
                </Card>
            </div>

            {error && !loading ? (
                <Alert
                    type="error"
                    showIcon
                    message="Dashboard yüklenemedi"
                    description={error}
                    style={{ marginBottom: 16 }}
                />
            ) : null}

            <Skeleton active loading={loading}>
                <Row gutter={[16, 16]}>
                    <Col xs={24} md={12} xl={6}>
                        <Card className="stat-card">
                            <Statistic
                                title="Toplam Senaryo"
                                value={dashboard?.counts.scenarios || 0}
                                prefix={<FileTextOutlined className="stat-icon blue" />}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} md={12} xl={6}>
                        <Card className="stat-card">
                            <Statistic
                                title="Test Paketi"
                                value={dashboard?.counts.test_suites || 0}
                                prefix={<FolderOpenOutlined className="stat-icon cyan" />}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} md={12} xl={6}>
                        <Card className="stat-card">
                            <Statistic
                                title="Üretilen Test Case"
                                value={dashboard?.counts.test_cases || 0}
                                valueStyle={{ color: '#52c41a' }}
                                prefix={<ExperimentOutlined className="stat-icon green" />}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} md={12} xl={6}>
                        <Card className="stat-card">
                            <Statistic
                                title="Girdi Dosyası"
                                value={dashboard?.counts.input_files || 0}
                                prefix={<DatabaseOutlined className="stat-icon orange" />}
                            />
                        </Card>
                    </Col>
                </Row>

                <Row gutter={[16, 16]} className="info-row">
                    <Col xs={24} xl={14}>
                        <Card
                            title={
                                <span>
                                    <ExperimentOutlined className="card-title-icon" />
                                    Generator Dağılımı
                                </span>
                            }
                            className="info-card"
                        >
                            {dashboard && dashboard.test_types.some((item) => item.case_count > 0) ? (
                                <div className="home-generator-list">
                                    {dashboard.test_types.map((item) => (
                                        <div key={item.key} className="home-generator-item">
                                            <div className="home-generator-top">
                                                <Space>
                                                    <Tag color={TYPE_COLORS[item.key]}>{item.label}</Tag>
                                                    <Text type="secondary">{item.suite_count} paket</Text>
                                                </Space>
                                                <Text strong>{item.case_count} case</Text>
                                            </div>
                                            <Progress
                                                percent={totalCases > 0 ? Math.round((item.case_count / totalCases) * 100) : 0}
                                                showInfo={false}
                                                strokeColor={
                                                    item.key === 'bsc'
                                                        ? '#1677ff'
                                                        : item.key === 'ngv'
                                                          ? '#52c41a'
                                                          : item.key === 'ngi'
                                                            ? '#f5222d'
                                                            : '#fa8c16'
                                                }
                                            />
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <Empty description="Henüz test çıktısı yok" />
                            )}
                        </Card>
                    </Col>
                    <Col xs={24} xl={10}>
                        <Card
                            title={
                                <span>
                                    <ThunderboltOutlined className="card-title-icon" />
                                    Hızlı Bakış
                                </span>
                            }
                            className="info-card"
                        >
                            <div className="home-summary-grid">
                                <div className="home-summary-item">
                                    <span className="home-summary-label">En yoğun generator</span>
                                    <strong>{topGenerator?.label || 'Henüz veri yok'}</strong>
                                </div>
                                <div className="home-summary-item">
                                    <span className="home-summary-label">Kaynak dağılımı</span>
                                    <Space size={[4, 8]} wrap>
                                        {dashboard?.input_breakdown.map((item) => (
                                            <Tag key={item.key} color="processing">
                                                {item.label}: {item.count}
                                            </Tag>
                                        ))}
                                    </Space>
                                </div>
                                <div className="home-summary-item">
                                    <span className="home-summary-label">Aksiyonlar</span>
                                    <Space wrap>
                                        <Link to="/scenarios/create">
                                            <Button type="primary" icon={<FileTextOutlined />}>
                                                Senaryo Oluştur
                                            </Button>
                                        </Link>
                                        <Link to="/tests/create">
                                            <Button icon={<ExperimentOutlined />}>
                                                Test Oluştur
                                            </Button>
                                        </Link>
                                        <Link to="/tests/list">
                                            <Button icon={<ApiOutlined />}>
                                                Çıktıları Aç
                                            </Button>
                                        </Link>
                                    </Space>
                                </div>
                            </div>
                        </Card>
                    </Col>
                </Row>

                <Row gutter={[16, 16]} className="info-row">
                    <Col xs={24} xl={12}>
                        <Card
                            title={
                                <span>
                                    <FileTextOutlined className="card-title-icon" />
                                    Son Oluşturulan Senaryolar
                                </span>
                            }
                            className="info-card"
                        >
                            <Table
                                rowKey="id"
                                columns={scenarioColumns}
                                dataSource={dashboard?.recent_scenarios || []}
                                pagination={false}
                                size="small"
                                locale={{ emptyText: 'Henüz senaryo yok' }}
                            />
                        </Card>
                    </Col>
                    <Col xs={24} xl={12}>
                        <Card
                            title={
                                <span>
                                    <ExperimentOutlined className="card-title-icon" />
                                    Son Test Paketleri
                                </span>
                            }
                            className="info-card"
                        >
                            <Table
                                rowKey="name"
                                columns={testColumns}
                                dataSource={dashboard?.recent_tests || []}
                                pagination={false}
                                size="small"
                                locale={{ emptyText: 'Henüz test paketi yok' }}
                            />
                        </Card>
                    </Col>
                </Row>
            </Skeleton>
        </div>
    );
};
