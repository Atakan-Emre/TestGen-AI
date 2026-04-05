import React, { useState } from 'react';
import { Table, Button, Space, Modal, message, Upload, Typography } from 'antd';
import { DeleteOutlined, EyeOutlined, UploadOutlined, SyncOutlined, FileExcelOutlined } from '@ant-design/icons';
import { useCsvFiles } from '../../hooks/useCsvFiles';

const { Title } = Typography;

interface CsvFile {
    id: number;
    name: string;
    content: string;
    created_at: string;
    updated_at: string | null;
}

export const CsvListPage: React.FC = () => {
    const { 
        csvFiles, 
        loading: isLoading, 
        deleteCsvFile,
        uploadCsvFile,
        syncCsvFiles,
        viewCsvFile,
        error 
    } = useCsvFiles();

    const [selectedFile, setSelectedFile] = useState<CsvFile | null>(null);
    const [isViewModalVisible, setIsViewModalVisible] = useState(false);
    const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);
    const [fileContent, setFileContent] = useState<string>('');

    const handleUpload = async (file: File) => {
        try {
            await uploadCsvFile(file);
            message.success('CSV dosyası başarıyla yüklendi');
        } catch (error) {
            message.error('CSV dosyası yüklenirken bir hata oluştu');
        }
    };

    const handleDelete = (file: CsvFile) => {
        setSelectedFile(file);
        setIsDeleteModalVisible(true);
    };

    const handleSync = async () => {
        try {
            await syncCsvFiles();
            message.success('CSV dosyaları başarıyla senkronize edildi');
        } catch (error) {
            message.error('CSV dosyaları senkronize edilirken bir hata oluştu');
        }
    };

    const handleView = async (file: CsvFile) => {
        try {
            await viewCsvFile(file.id);
            setSelectedFile(file);
            setIsViewModalVisible(true);
        } catch (error) {
            message.error('CSV içeriği alınırken bir hata oluştu');
        }
    };

    const confirmDelete = async () => {
        if (selectedFile) {
            try {
                await deleteCsvFile(selectedFile.id);
                message.success('CSV dosyası başarıyla silindi');
                setIsDeleteModalVisible(false);
            } catch (error) {
                console.error('Silme hatası:', error);
                message.error('CSV dosyası silinirken hata oluştu');
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
                    <FileExcelOutlined style={{ color: '#52c41a' }} />
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
            render: (_: any, record: CsvFile) => (
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

    return (
        <div style={{ padding: '24px' }}>
            <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Title level={2}>
                    <FileExcelOutlined /> CSV Dosyaları
                </Title>
                <Space>
                    <Upload
                        accept=".csv"
                        showUploadList={false}
                        beforeUpload={(file) => {
                            handleUpload(file);
                            return false;
                        }}
                    >
                        <Button type="primary" icon={<UploadOutlined />}>
                            CSV Yükle
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
            
            <Table
                columns={columns}
                dataSource={csvFiles}
                loading={isLoading}
                rowKey="id"
            />

            {/* Görüntüleme Modalı */}
            <Modal
                title={
                    <Space>
                        <FileExcelOutlined />
                        {selectedFile?.name || ''} Detayı
                    </Space>
                }
                open={isViewModalVisible}
                onCancel={() => setIsViewModalVisible(false)}
                width={800}
                footer={null}
            >
                <pre style={{ 
                    maxHeight: '500px', 
                    overflow: 'auto',
                    whiteSpace: 'pre-wrap',
                    wordWrap: 'break-word',
                    backgroundColor: '#f5f5f5',
                    padding: '12px',
                    borderRadius: '4px'
                }}>
                    {fileContent}
                </pre>
            </Modal>

            {/* Silme Onay Modalı */}
            <Modal
                title={
                    <Space>
                        <DeleteOutlined style={{ color: '#ff4d4f' }} />
                        CSV Dosyası Silme
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