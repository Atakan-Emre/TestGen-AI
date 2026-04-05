import React, { useState, useEffect } from 'react';
import { 
    Alert,
    Card, 
    Table, 
    Button, 
    Space, 
    Input, 
    Modal, 
    message, 
    Upload,
    App,
    Tooltip
} from 'antd';
import {
    EyeOutlined,
    DeleteOutlined,
    UploadOutlined,
    EditOutlined,
    SaveOutlined,
    SyncOutlined,
    FileAddOutlined
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import type { TableProps } from 'antd';
import axios from 'axios';
import { API_URL, IS_DEMO_MODE } from '../../config';
import {
    DEMO_MODE_DESCRIPTION,
    DEMO_MODE_TITLE,
    DEMO_MUTATION_MESSAGE,
    demoVariableFiles,
    getDemoVariableFileContent,
} from '../../demo/demoData';

const { Search } = Input;
const { TextArea } = Input;

interface VariableFile {
    id: number;
    name: string;
    size: number;
    created_at: number;
    updated_at: number;
    type: string;
    content?: string;
}

export const VariablesPage: React.FC = () => {
    const [messageApi, messageContextHolder] = message.useMessage();
    const [modal, modalContextHolder] = Modal.useModal();
    const [files, setFiles] = useState<VariableFile[]>([]);
    const [loading, setLoading] = useState(false);
    const [searchText, setSearchText] = useState('');
    const [viewModalVisible, setViewModalVisible] = useState(false);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [selectedFile, setSelectedFile] = useState<VariableFile | null>(null);
    const [editContent, setEditContent] = useState('');

    const fetchFiles = async () => {
        try {
            setLoading(true);
            if (IS_DEMO_MODE) {
                setFiles(demoVariableFiles);
                return;
            }
            const response = await axios.get(`${API_URL}/files/variables`);
            if (response.data.files) {
                setFiles(response.data.files);
                messageApi.success('Değişken dosyaları başarıyla yüklendi');
            } else {
                throw new Error('Dosyalar yüklenemedi');
            }
        } catch (error) {
            console.error('Dosyalar yüklenirken hata:', error);
            messageApi.error('Dosyalar yüklenirken bir hata oluştu');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchFiles();
    }, []);

    const handleSearch = (value: string) => {
        setSearchText(value);
    };

    const handleView = async (file: VariableFile) => {
        try {
            if (IS_DEMO_MODE) {
                setSelectedFile({
                    ...file,
                    content: getDemoVariableFileContent(file.name)
                });
                setViewModalVisible(true);
                return;
            }
            const response = await axios.get(`${API_URL}/files/variables/${file.name}`);
            if (response.data.content) {
                setSelectedFile({
                    ...file,
                    content: response.data.content
                });
                setViewModalVisible(true);
            } else {
                messageApi.error('Dosya içeriği yüklenemedi');
            }
        } catch (error) {
            console.error('Dosya içeriği yüklenirken hata:', error);
            messageApi.error('Dosya içeriği yüklenirken bir hata oluştu');
        }
    };

    const handleEdit = async (file: VariableFile) => {
        try {
            if (IS_DEMO_MODE) {
                const content = getDemoVariableFileContent(file.name);
                setSelectedFile({
                    ...file,
                    content
                });
                setEditContent(content);
                setEditModalVisible(true);
                return;
            }
            const response = await axios.get(`${API_URL}/files/variables/${file.name}`);
            if (response.data.content) {
                setSelectedFile({
                    ...file,
                    content: response.data.content
                });
                setEditContent(response.data.content);
                setEditModalVisible(true);
            } else {
                messageApi.error('Dosya içeriği yüklenemedi');
            }
        } catch (error) {
            console.error('Dosya içeriği yüklenirken hata:', error);
            messageApi.error('Dosya içeriği yüklenirken bir hata oluştu');
        }
    };

    const handleSave = async () => {
        if (!selectedFile) return;

        try {
            if (IS_DEMO_MODE) {
                messageApi.info(DEMO_MUTATION_MESSAGE);
                return;
            }
            const response = await axios.put(
                `${API_URL}/files/variables/${selectedFile.name}`,
                editContent,
                {
                    headers: {
                        'Content-Type': 'text/plain'
                    }
                }
            );
            messageApi.success(response.data.message);
            setEditModalVisible(false);
            fetchFiles();
        } catch (error) {
            console.error('Dosya güncellenirken hata:', error);
            messageApi.error('Dosya güncellenirken bir hata oluştu');
        }
    };

    const handleCreateNew = () => {
        setSelectedFile(null);
        setEditContent('');
        setEditModalVisible(true);
    };

    const handleSaveNew = async () => {
        try {
            if (IS_DEMO_MODE) {
                messageApi.info(DEMO_MUTATION_MESSAGE);
                return;
            }
            // Yeni dosya adını al
            const fileName = await new Promise<string>((resolve, reject) => {
                modal.confirm({
                    title: 'Dosya Adı',
                    content: (
                        <Input 
                            placeholder="örnek: yeni_değişkenler.txt"
                            onChange={(e) => {
                                const value = e.target.value;
                                if (!value.endsWith('.txt')) {
                                    e.target.value = value + '.txt';
                                }
                            }}
                        />
                    ),
                    onOk: () => {
                        const input = document.querySelector('.ant-modal-content input') as HTMLInputElement;
                        let value = input.value;
                        if (!value.endsWith('.txt')) {
                            value += '.txt';
                        }
                        resolve(value);
                    },
                    onCancel: () => reject('İptal edildi'),
                    okText: 'Oluştur',
                    cancelText: 'İptal'
                });
            });

            // Yeni dosya oluştur
            const response = await axios.put(
                `${API_URL}/files/variables/${fileName}`,
                editContent,
                {
                    headers: {
                        'Content-Type': 'text/plain'
                    }
                }
            );

            messageApi.success(response.data.message);
            setEditModalVisible(false);
            fetchFiles();

        } catch (error) {
            if (error !== 'İptal edildi') {
                console.error('Dosya oluşturulurken hata:', error);
                messageApi.error('Dosya oluşturulurken bir hata oluştu');
            }
        }
    };

    const handleDelete = async (fileName: string) => {
        try {
            if (IS_DEMO_MODE) {
                messageApi.info(DEMO_MUTATION_MESSAGE);
                return;
            }
            await new Promise<boolean>((resolve) => {
                modal.confirm({
                    title: 'Silme Onayı',
                    content: `"${fileName}" dosyasını silmek istediğinize emin misiniz?`,
                    okText: 'Evet',
                    cancelText: 'İptal',
                    async onOk() {
                        try {
                            const response = await axios.delete(`${API_URL}/files/variables/${fileName}`);
                            messageApi.success(response.data.message);
                            fetchFiles();
                            resolve(true);
                        } catch (error: any) {
                            const errorMessage = error.response?.data?.detail || error.message;
                            messageApi.error(`Dosya silinirken bir hata oluştu: ${errorMessage}`);
                            resolve(false);
                        }
                    },
                    onCancel() {
                        resolve(false);
                    }
                });
            });
        } catch (error) {
            console.error('Silme hatası:', error);
            messageApi.error('Silme işlemi başlatılırken bir hata oluştu');
        }
    };

    const uploadProps: UploadProps = {
        name: 'file',
        action: `${API_URL}/files/upload`,
        accept: '.txt,.json,.yaml,.yml',
        showUploadList: false,
        beforeUpload() {
            if (IS_DEMO_MODE) {
                messageApi.info(DEMO_MUTATION_MESSAGE);
                return false;
            }
            return true;
        },
        onChange(info) {
            if (info.file.status === 'done') {
                messageApi.success(`${info.file.name} başarıyla yüklendi`);
                fetchFiles();
            } else if (info.file.status === 'error') {
                messageApi.error(`${info.file.name} yüklenirken hata oluştu`);
            }
        }
    };

    const columns: TableProps<VariableFile>['columns'] = [
        {
            title: 'Dosya Adı',
            dataIndex: 'name',
            key: 'name',
            filteredValue: [searchText],
            onFilter: (value, record) => 
                record.name.toLowerCase().includes(value.toString().toLowerCase())
        },
        {
            title: 'Format',
            dataIndex: 'type',
            key: 'type',
            render: (type) => type.toUpperCase()
        },
        {
            title: 'Boyut',
            dataIndex: 'size',
            key: 'size',
            render: (size) => `${Math.round(size / 1024)} KB`
        },
        {
            title: 'Güncelleme Tarihi',
            dataIndex: 'updated_at',
            key: 'updated_at',
            render: (date) => new Date(date * 1000).toLocaleString(),
            sorter: (a, b) => a.updated_at - b.updated_at
        },
        {
            title: 'İşlemler',
            key: 'actions',
            render: (_, record) => (
                <Space>
                    <Tooltip title="Görüntüle">
                        <Button 
                            icon={<EyeOutlined />} 
                            onClick={() => handleView(record)}
                        />
                    </Tooltip>
                    <Tooltip title="Düzenle">
                        <Button 
                            type="primary"
                            icon={<EditOutlined />}
                            onClick={() => handleEdit(record)}
                            disabled={IS_DEMO_MODE}
                        />
                    </Tooltip>
                    <Tooltip title="Sil">
                        <Button 
                            danger 
                            icon={<DeleteOutlined />}
                            onClick={() => handleDelete(record.name)}
                            disabled={IS_DEMO_MODE}
                        />
                    </Tooltip>
                </Space>
            )
        }
    ];

    return (
        <App>
            {messageContextHolder}
            {modalContextHolder}
            <div style={{ padding: '24px' }}>
                <Card title="Değişken Değerleri">
                    <Space direction="vertical" style={{ width: '100%' }} size="large">
                        {IS_DEMO_MODE ? (
                            <Alert
                                type="info"
                                showIcon
                                message={DEMO_MODE_TITLE}
                                description={DEMO_MODE_DESCRIPTION}
                            />
                        ) : null}
                        <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                            <Space>
                                <Search
                                    placeholder="Dosya adı ile ara..."
                                    onSearch={handleSearch}
                                    style={{ width: 300 }}
                                    allowClear
                                />
                                <Button 
                                    type="primary"
                                    icon={<SyncOutlined />}
                                    onClick={fetchFiles}
                                    loading={loading}
                                >
                                    Yenile
                                </Button>
                            </Space>
                            <Space>
                                <Button 
                                    type="primary"
                                    icon={<FileAddOutlined />}
                                    onClick={handleCreateNew}
                                    disabled={IS_DEMO_MODE}
                                >
                                    Yeni Dosya Oluştur
                                </Button>
                                <Upload {...uploadProps}>
                                    <Button icon={<UploadOutlined />} disabled={IS_DEMO_MODE}>Dosya Yükle</Button>
                                </Upload>
                            </Space>
                        </Space>

                        <Table
                            columns={columns}
                            dataSource={files}
                            rowKey="name"
                        />
                    </Space>
                </Card>

                <Modal
                    title="Değişken Görüntüleyici"
                    open={viewModalVisible}
                    onCancel={() => setViewModalVisible(false)}
                    footer={null}
                    width={800}
                >
                    <pre style={{ 
                        background: '#f0f0f0', 
                        padding: 16, 
                        borderRadius: 4,
                        maxHeight: '60vh',
                        overflow: 'auto'
                    }}>
                        {selectedFile?.content}
                    </pre>
                </Modal>

                <Modal
                    title={selectedFile ? "Değişken Düzenleyici" : "Yeni Değişken Dosyası"}
                    open={editModalVisible}
                    onCancel={() => setEditModalVisible(false)}
                    footer={[
                        <Button key="cancel" onClick={() => setEditModalVisible(false)}>
                            İptal
                        </Button>,
                        <Button 
                            key="save" 
                            type="primary" 
                            icon={<SaveOutlined />}
                            onClick={selectedFile ? handleSave : handleSaveNew}
                            disabled={IS_DEMO_MODE}
                        >
                            Kaydet
                        </Button>
                    ]}
                    width={800}
                >
                    <TextArea
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        rows={15}
                        style={{ fontFamily: 'monospace' }}
                        placeholder="Değişken değerlerini buraya yazın..."
                    />
                </Modal>
            </div>
        </App>
    );
}; 
