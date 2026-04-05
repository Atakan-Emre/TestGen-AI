import React, { useState } from 'react';
import { Card, Select, Button, Table, Tag, Space } from 'antd';

const { Option } = Select;

export const TestRunPage: React.FC = () => {
    const [selectedScenario, setSelectedScenario] = useState<string>();
    const [selectedTemplate, setSelectedTemplate] = useState<string>();

    return (
        <div>
            <h2>Test Çalıştır</h2>

            <Card title="Test Ayarları" style={{ marginBottom: 24 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                        <label>Test Senaryosu Seç:</label>
                        <Select 
                            style={{ width: '100%' }} 
                            placeholder="Senaryo seçin"
                            onChange={setSelectedScenario}
                        >
                            <Option value="1">Login Testi (BSC)</Option>
                            <Option value="2">Kayıt Testi (NGI)</Option>
                        </Select>
                    </div>

                    <div>
                        <label>JSON Template Seç:</label>
                        <Select 
                            style={{ width: '100%' }} 
                            placeholder="Template seçin"
                            onChange={setSelectedTemplate}
                        >
                            <Option value="1">login.json</Option>
                            <Option value="2">register.json</Option>
                        </Select>
                    </div>

                    <Button 
                        type="primary" 
                        disabled={!selectedScenario || !selectedTemplate}
                    >
                        Testi Başlat
                    </Button>
                </Space>
            </Card>

            <Card title="Son Çalıştırılan Testler">
                <Table 
                    columns={[
                        {
                            title: 'Senaryo',
                            dataIndex: 'scenario',
                            key: 'scenario',
                        },
                        {
                            title: 'Durum',
                            dataIndex: 'status',
                            key: 'status',
                            render: (status: string) => (
                                <Tag color={status === 'SUCCESS' ? 'success' : 'error'}>
                                    {status}
                                </Tag>
                            ),
                        },
                        {
                            title: 'Tarih',
                            dataIndex: 'date',
                            key: 'date',
                        },
                    ]}
                    // dataSource={recentTests}
                />
            </Card>
        </div>
    );
}; 