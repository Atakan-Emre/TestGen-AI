import React, { useState } from 'react';
import { Table, Button, Space, Upload, Modal, Typography, App, Alert } from 'antd';
import { 
    UploadOutlined, 
    DeleteOutlined, 
    FileTextOutlined, 
    EyeOutlined, 
    SyncOutlined,
    FileExcelOutlined
} from '@ant-design/icons';
import { useCsvFiles } from '../../hooks/useCsvFiles';
import type { CsvFile } from '../../hooks/useCsvFiles';
import { IS_DEMO_MODE } from '../../config';
import { DEMO_MODE_DESCRIPTION, DEMO_MODE_TITLE } from '../../demo/demoData';

const { Title } = Typography;

export const CsvFilesPage: React.FC = () => {
    const { message } = App.useApp();
    const { 
        csvFiles, 
        selectedFile: viewedFile,
        loading: isLoading, 
        uploadCsvFile: uploadCsv, 
        deleteCsvFile: deleteCsv,
        viewCsvFile,
        syncCsvFiles,
        error 
    } = useCsvFiles();

    const [selectedFile, setSelectedFile] = useState<CsvFile | null>(null);
    const [isViewModalVisible, setIsViewModalVisible] = useState(false);
    const [isDeleteModalVisible, setIsDeleteModalVisible] = useState(false);

    const handleUpload = async (file: File) => {
        try {
            await uploadCsv(file);
            message.success('CSV dosyası başarıyla yüklendi');
        } catch (error) {
            message.error('CSV dosyası yüklenirken bir hata oluştu');
        }
    };

    const handleDelete = (file: CsvFile) => {
        setSelectedFile(file);
        setIsDeleteModalVisible(true);
    };

    const confirmDelete = async () => {
        if (selectedFile) {
            try {
                await deleteCsv(selectedFile.id);
                message.success('CSV dosyası başarıyla silindi');
                setIsDeleteModalVisible(false);
            } catch (error) {
                console.error('Silme hatası:', error);
                message.error('CSV dosyası silinirken hata oluştu');
            }
        }
    };

    const handleSync = async () => {
        try {
            const key = 'sync';
            message.loading({ content: 'Dosyalar senkronize ediliyor...', key });
            await syncCsvFiles();
            message.success({ content: 'Dosyalar başarıyla senkronize edildi', key });
        } catch (error) {
            message.error('Dosyalar senkronize edilirken bir hata oluştu');
        }
    };

    const handleView = async (file: CsvFile) => {
        try {
            await viewCsvFile(file.id);
            setSelectedFile(file);
            setIsViewModalVisible(true);
        } catch (error) {
            console.error('Görüntüleme hatası:', error);
            message.error('CSV içeriği görüntülenirken bir hata oluştu');
        }
    };

    const columns = [
        {
            title: 'Dosya Adı',
            dataIndex: 'name',
            key: 'name',
            render: (text: string) => (
                <Space>
                    <FileExcelOutlined className="file-icon csv" />
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
                        disabled={IS_DEMO_MODE}
                    >
                        Sil
                    </Button>
                </Space>
            ),
        },
    ];

    return (
        <App>
            <div style={{ padding: '24px' }}>
                <div className="page-container">
                    <div className="page-header">
                        <Title level={2}>
                            <FileExcelOutlined /> CSV Dosyaları
                        </Title>
                        <Space>
                            <Upload
                                accept=".csv"
                                showUploadList={false}
                                disabled={IS_DEMO_MODE}
                                beforeUpload={(file) => {
                                    handleUpload(file);
                                    return false;
                                }}
                            >
                                <Button type="primary" icon={<UploadOutlined />} disabled={IS_DEMO_MODE}>
                                    CSV Yükle
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
                        dataSource={csvFiles}
                        loading={isLoading}
                        rowKey="id"
                        className="data-table"
                    />

                    {/* Görüntüleme Modalı */}
                    <Modal
                        title={
                            <Space>
                                <FileExcelOutlined />
                                {(viewedFile || selectedFile)?.name || ''} Detayı
                            </Space>
                        }
                        open={isViewModalVisible}
                        onCancel={() => setIsViewModalVisible(false)}
                        width={800}
                        footer={null}
                    >
                        <pre className="content-preview">
                            {(viewedFile || selectedFile)?.content}
                        </pre>
                    </Modal>

                    {/* Silme Onay Modalı */}
                    <Modal
                        title={
                            <Space>
                                <DeleteOutlined className="modal-icon delete" />
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
                            <DeleteOutlined className="modal-icon delete large" />
                            <p>
                                <strong>{selectedFile?.name}</strong> dosyasını silmek istediğinizden emin misiniz?
                                <br />
                                Bu işlem geri alınamaz.
                            </p>
                        </Space>
                    </Modal>
                </div>
            </div>
        </App>
    );
}; 
