import React from 'react';
import { Table, Tag, Button, Space } from 'antd';
import { EyeOutlined, DownloadOutlined } from '@ant-design/icons';

interface TestResult {
    id: number;
    scenario_name: string;
    test_type: 'BSC' | 'NGI' | 'OPT' | 'NGV';
    status: 'SUCCESS' | 'FAILED' | 'ERROR';
    created_at: string;
    json_output: any;
}

export const TestResultsPage: React.FC = () => {
    const columns = [
        {
            title: 'Senaryo',
            dataIndex: 'scenario_name',
            key: 'scenario_name',
        },
        {
            title: 'Test Tipi',
            dataIndex: 'test_type',
            key: 'test_type',
            render: (type: string) => (
                <Tag color={
                    type === 'BSC' ? 'green' :
                    type === 'NGI' ? 'red' :
                    type === 'OPT' ? 'blue' :
                    'purple'
                }>
                    {type}
                </Tag>
            ),
        },
        {
            title: 'Durum',
            dataIndex: 'status',
            key: 'status',
            render: (status: string) => (
                <Tag color={
                    status === 'SUCCESS' ? 'success' :
                    status === 'FAILED' ? 'error' :
                    'warning'
                }>
                    {status}
                </Tag>
            ),
        },
        {
            title: 'Tarih',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleString('tr-TR'),
        },
        {
            title: 'İşlemler',
            key: 'actions',
            render: (record: TestResult) => (
                <Space>
                    <Button
                        icon={<EyeOutlined />}
                        onClick={() => handleView(record)}
                    >
                        Görüntüle
                    </Button>
                    <Button
                        icon={<DownloadOutlined />}
                        onClick={() => handleDownload(record)}
                    >
                        İndir
                    </Button>
                </Space>
            ),
        },
    ];

    const handleView = (result: TestResult) => {
        // JSON görüntüleme modalı
    };

    const handleDownload = (result: TestResult) => {
        // JSON indirme işlemi
    };

    return (
        <div style={{ padding: '24px' }}>
            <h1>Test Sonuçları</h1>
            
            <Table<TestResult>
                columns={columns}
                // dataSource={results}  // API'den gelecek
                rowKey="id"
            />
        </div>
    );
}; 