import React, { useState } from 'react';
import { Table, Button, Space, Modal, message } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { useScenarios } from '../../hooks/useScenarios';
import { useCategories } from '../../hooks/useCategories';
import { ScenarioForm } from './ScenarioForm';
import { Scenario } from '../../api/types';

export const ScenariosPage: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingScenario, setEditingScenario] = useState<Scenario | null>(null);
    const { scenarios, loading, createScenario, updateScenario, deleteScenario } = useScenarios();
    const { categories } = useCategories();

    const columns = [
        {
            title: 'İsim',
            dataIndex: 'name',
            key: 'name',
        },
        {
            title: 'Kategori',
            key: 'category',
            render: (record: Scenario) => {
                const category = categories?.find((c: any) => c.id === record.csv_file_id);
                return category?.name || '-';
            },
        },
        {
            title: 'Açıklama',
            dataIndex: 'description',
            key: 'description',
        },
        {
            title: 'Beklenen Sonuç',
            dataIndex: 'expected_result',
            key: 'expected_result',
        },
        {
            title: 'İşlemler',
            key: 'actions',
            render: (record: Scenario) => (
                <Space>
                    <Button
                        icon={<EditOutlined />}
                        onClick={() => handleEdit(record)}
                    />
                    <Button
                        icon={<PlayCircleOutlined />}
                        onClick={() => handleRun(record)}
                    />
                    <Button
                        danger
                        icon={<DeleteOutlined />}
                        onClick={() => handleDelete(record)}
                    />
                </Space>
            ),
        },
    ];

    const handleEdit = (scenario: Scenario) => {
        setEditingScenario(scenario);
        setIsModalOpen(true);
    };

    const handleRun = (scenario: Scenario) => {
        // Test çalıştırma işlemi eklenecek
        message.info('Test çalıştırma özelliği yakında eklenecek');
    };

    const handleDelete = (scenario: Scenario) => {
        Modal.confirm({
            title: 'Senaryoyu Sil',
            content: `"${scenario.name}" senaryosunu silmek istediğinize emin misiniz?`,
            okText: 'Evet',
            cancelText: 'İptal',
            onOk: async () => {
                try {
                    await deleteScenario(scenario.id);
                    message.success('Senaryo başarıyla silindi');
                } catch (error) {
                    message.error('Senaryo silinirken bir hata oluştu');
                }
            },
        });
    };

    const handleSubmit = async (values: any) => {
        try {
            if (editingScenario) {
                await updateScenario(editingScenario.id, values);
                message.success('Senaryo başarıyla güncellendi');
            } else {
                await createScenario(values);
                message.success('Senaryo başarıyla oluşturuldu');
            }
            setIsModalOpen(false);
            setEditingScenario(null);
        } catch (error) {
            message.error('Bir hata oluştu');
        }
    };

    return (
        <div>
            <div style={{ marginBottom: 16 }}>
                <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setIsModalOpen(true)}
                >
                    Yeni Senaryo
                </Button>
            </div>

            <Table
                columns={columns}
                dataSource={scenarios}
                loading={loading}
                rowKey="id"
            />

            <ScenarioForm
                open={isModalOpen}
                onCancel={() => {
                    setIsModalOpen(false);
                    setEditingScenario(null);
                }}
                onSubmit={handleSubmit}
                initialValues={editingScenario}
                loading={loading}
                categories={categories || []}
            />
        </div>
    );
}; 