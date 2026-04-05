import React, { useState } from 'react';
import { Table, Button, Space, Upload, Modal, Typography, App, Alert } from 'antd';
import { 
    UploadOutlined, 
    DeleteOutlined, 
    FileTextOutlined, 
    EyeOutlined, 
    SyncOutlined,
    CodeOutlined
} from '@ant-design/icons';
import { useJsonFiles } from '../../hooks/useJsonFiles';
import type { JsonFile } from '../../hooks/useJsonFiles';
import { JsonViewer } from '@textea/json-viewer';
import { IS_DEMO_MODE } from '../../config';
import { DEMO_MODE_DESCRIPTION, DEMO_MODE_TITLE } from '../../demo/demoData';

const { Title } = Typography;

export const JsonFilesPage: React.FC = () => {
    const { message } = App.useApp();
    const { 
        jsonFiles, 
        selectedFile: viewedFile,
        loading: isLoading, 
        deleteJsonFile,
        uploadJsonFile,
        syncJsonFiles,
        viewJsonFile,
        error 
    } = useJsonFiles();

    const [selectedFile, setSelectedFile] = useState<JsonFile | null>(null);
    const [isViewModalVisible, setIsViewModalVisible] = useState(false);
    const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

    const handleUpload = async (file: File) => {
        try {
            await uploadJsonFile(file);
            message.success('JSON dosyası başarıyla yüklendi');
        } catch (error) {
            message.error('JSON dosyası yüklenirken bir hata oluştu');
        }
    };

    const handleDelete = (file: JsonFile) => {
        setSelectedFile(file);
        setIsDeleteModalVisible(true);
    };

    const handleSync = async () => {
        try {
            await syncJsonFiles();
            message.success('JSON dosyaları başarıyla senkronize edildi');
        } catch (error) {
            message.error('JSON dosyaları senkronize edilirken bir hata oluştu');
        }
    };

    const handleView = async (file: JsonFile) => {
        try {
            await viewJsonFile(file.id);
            setSelectedFile(file);
            setIsViewModalVisible(true);
        } catch (error) {
            message.error('JSON içeriği alınırken bir hata oluştu');
        }
    };

    const confirmDelete = async () => {
        if (selectedFile) {
            try {
                await deleteJsonFile(selectedFile.id);
                message.success('JSON dosyası başarıyla silindi');
                setIsDeleteModalVisible(false);
            } catch (error) {
                console.error('Silme hatası:', error);
                message.error('JSON dosyası silinirken hata oluştu');
            }
        }
    };

    const columns = [
        {
            title: 'Dosya Adı',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => (
                <Space>
                    <CodeOutlined style={{ color: '#1890ff' }} />
                    {text}
                </Space>
            )
        },
        {
            title: 'Oluşturma Tarihi',
            dataIndex: 'created_at',
            key: 'created_at',
            render: (date: string) => new Date(date).toLocaleString('tr-TR')
        },
        {
            title: 'İşlemler',
            key: 'actions',
            render: (_: any, record: JsonFile) => (
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
                        disabled={IS_DEMO_MODE}
                    >
                        Sil
                    </Button>
                </Space>
            ),
        },
    ];

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Title level={2}>
                    <CodeOutlined /> JSON Dosyaları
                </Title>
                <Space>
                    <Upload
                        accept=".json"
                        showUploadList={false}
                        disabled={IS_DEMO_MODE}
                        beforeUpload={(file) => {
                            handleUpload(file);
                            return false;
                        }}
                    >
                        <Button type="primary" icon={<UploadOutlined />} disabled={IS_DEMO_MODE}>
                            JSON Yükle
                        </Button>
                    </Upload>
                    <Button 
                        icon={<SyncOutlined />} 
                        onClick={handleSync}
                        disabled={IS_DEMO_MODE}
                    >
                        Senkronize Et
                    </Button>
                </Space>
            </div>

            {IS_DEMO_MODE ? (
                <Alert
                    type="info"
                    showIcon
                    style={{ marginBottom: 16 }}
                    message={DEMO_MODE_TITLE}
                    description={DEMO_MODE_DESCRIPTION}
                />
            ) : null}
            
            <Table
                columns={columns}
                dataSource={jsonFiles}
                loading={isLoading}
                rowKey="id"
            />

            {/* Görüntüleme Modalı */}
            <Modal
                title={
                    <Space>
                        <CodeOutlined />
                        {(viewedFile || selectedFile)?.name || ''} Detayı
                    </Space>
                }
                open={isViewModalVisible}
                onCancel={() => setIsViewModalVisible(false)}
                width={800}
                footer={null}
            >
                {(viewedFile || selectedFile)?.content && (
                    <JsonViewer 
                        value={
                            typeof (viewedFile || selectedFile)?.content === 'string' 
                                ? JSON.parse((viewedFile || selectedFile)?.content as string)
                                : (viewedFile || selectedFile)?.content
                        }
                        rootName={false}
                        displayDataTypes={false}
                        displaySize={false}
                        enableClipboard={true}
                        theme="light"
                    />
                )}
            </Modal>

            {/* Silme Onay Modalı */}
            <Modal
                title={
                    <Space>
                        <DeleteOutlined style={{ color: '#ff4d4f' }} />
                        JSON Dosyası Silme
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
                        <strong>{selectedFile?.name}</strong> dosyasını silmek istediğinizden emin misiniz?
                        <br />
                        Bu işlem geri alınamaz.
                    </p>
                </Space>
            </Modal>
        </div>
    );
}; 
