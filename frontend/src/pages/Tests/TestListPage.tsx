import React, { useState, useEffect } from 'react';
import { 
    Card, 
    Table, 
    Button, 
    Space, 
    Tag, 
    Input, 
    Collapse, 
    Modal, 
    message,
    Tooltip,
    App,
    Typography
} from 'antd';
import {
    EyeOutlined,
    DeleteOutlined,
    DownloadOutlined,
    SyncOutlined
} from '@ant-design/icons';
import type { TableProps } from 'antd';
import axios from 'axios';
import { API_URL } from '../../config';

const { Panel } = Collapse;
const { Search } = Input;
const { Text } = Typography;

interface JsonFile {
    name: string;
    type: 'bsc' | 'ngv' | 'ngi' | 'opt';
    content?: string;
    created_at: string;
    description?: string;
    scenario_type?: string;
    expected_result?: string;
    expected_message?: string;
    file_path?: string;
    test_name?: string;
}

interface TestGroup {
    test_name: string;
    created_at: string;
    files: JsonFile[];
}

interface TestDirectory {
    name: string;
    created_at: string;
}

const TYPE_COLORS = {
    bsc: 'blue',
    ngv: 'green',
    ngi: 'red',
    opt: 'orange'
};

const TYPE_LABELS = {
    bsc: 'Temel Testler',
    ngv: 'Negatif Değer',
    ngi: 'Negatif Geçersiz',
    opt: 'Opsiyonel Testler'
};

const EXPECTED_RESULT_COLORS: Record<string, string> = {
    SUCCESS: 'green',
    VALIDATION_ERROR: 'red'
};

export const TestListPage: React.FC = () => {
    const [messageApi, messageContextHolder] = message.useMessage();
    const [modal, modalContextHolder] = Modal.useModal();
    const [searchText, setSearchText] = useState('');
    const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
    const [viewModalVisible, setViewModalVisible] = useState(false);
    const [selectedJson, setSelectedJson] = useState<string>('');
    const [testGroups, setTestGroups] = useState<TestGroup[]>([]);
    const [loading, setLoading] = useState(false);
    const [directories, setDirectories] = useState<TestDirectory[]>([]);

    const fetchTestGroups = async () => {
        try {
            setLoading(true);
            // Önce tüm klasörleri al
            const dirResponse = await axios.get(`${API_URL}/tests/list-directories`);
            const directories = dirResponse.data;

            const groups: TestGroup[] = [];
            
            for (const dir of directories) {
                const testFiles: JsonFile[] = [];
                
                // BSC testlerini al
                try {
                    const bscResponse = await axios.get(`${API_URL}/tests/bsc/list/${dir.name}`);
                    testFiles.push(...bscResponse.data.map((file: any) => ({
                        ...file,
                        type: 'bsc',
                        test_name: dir.name
                    })));
                } catch {
                }

                // NGV testlerini al
                try {
                    const ngvResponse = await axios.get(`${API_URL}/tests/ngv/list/${dir.name}`);
                    testFiles.push(...ngvResponse.data.map((file: any) => ({
                        ...file,
                        type: 'ngv',
                        test_name: dir.name
                    })));
                } catch {
                }

                // NGI testlerini al
                try {
                    const ngiResponse = await axios.get(`${API_URL}/tests/ngi/list/${dir.name}`);
                    testFiles.push(...ngiResponse.data.map((file: any) => ({
                        ...file,
                        type: 'ngi',
                        test_name: dir.name
                    })));
                } catch {
                }

                // OPT testlerini al
                try {
                    const optResponse = await axios.get(`${API_URL}/tests/opt/list/${dir.name}`);
                    testFiles.push(...optResponse.data.map((file: any) => ({
                        ...file,
                        type: 'opt',
                        test_name: dir.name
                    })));
                } catch {
                }

                // Boş olsa bile klasörü ekle
                groups.push({
                    test_name: dir.name,
                    created_at: dir.created_at,
                    files: testFiles
                });
            }

            setTestGroups(groups);
        } catch (error) {
            console.error('Test sonuçları yüklenirken hata:', error);
            messageApi.error('Test sonuçları yüklenirken bir hata oluştu');
        } finally {
            setLoading(false);
        }
    };

    const fetchDirectories = async () => {
        try {
            const response = await axios.get(`${API_URL}/tests/list-directories`);
            setDirectories(response.data);
        } catch (error) {
            console.error('Klasörler listelenirken hata:', error);
            messageApi.error('Klasörler listelenirken bir hata oluştu');
        }
    };

    const handleSearch = (value: string) => {
        setSearchText(value);
    };

    const fetchFileContent = async (file: JsonFile) => {
        if (file.content) {
            return file.content;
        }

        const response = await axios.get(
            `${API_URL}/tests/${file.type}/file/${file.test_name}/${file.name}`
        );
        return response.data.content;
    };

    const handleView = async (file: JsonFile) => {
        try {
            const content = await fetchFileContent(file);
            const parsedJson = typeof content === 'string' ? JSON.parse(content) : content;
            setSelectedJson(JSON.stringify(parsedJson, null, 2));
            setViewModalVisible(true);
        } catch (error) {
            messageApi.error('Geçersiz JSON formatı');
            console.error('JSON parse hatası:', error);
        }
    };

    const handleDownload = async (file: JsonFile) => {
        try {
            const content = await fetchFileContent(file);
            const element = document.createElement('a');
            const fileData = new Blob([content], {type: 'application/json'});
            element.href = URL.createObjectURL(fileData);
            element.download = file.name;
            document.body.appendChild(element);
            element.click();
            document.body.removeChild(element);
            messageApi.success('Dosya indirme başarılı');
        } catch (error) {
            console.error('Dosya indirme hatası:', error);
            messageApi.error('Dosya indirilirken bir hata oluştu');
        }
    };

    const handleDelete = async (fileNames: string[]) => {
        try {
            await new Promise<boolean>((resolve) => {
                modal.confirm({
                    title: 'Silme Onayı',
                    content: `${fileNames.length} adet dosyayı silmek istediğinize emin misiniz?`,
                    okText: 'Evet',
                    cancelText: 'İptal',
                    async onOk() {
                        try {
                            for (const fileName of fileNames) {
                                // Dosya tipini ve test adını bul
                                const file = testGroups
                                    .flatMap(group => group.files)
                                    .find(f => f.name === fileName);
                                
                                if (file) {
                                    const testGroup = testGroups.find(group => 
                                        group.files.some(f => f.name === fileName)
                                    );

                                    if (testGroup) {
                                        // Dosya yolunu düzelt
                                        const filePath = `${testGroup.test_name}/${file.type}/${fileName}`;
                                        
                                        try {
                                            // Silme isteği gönder
                                            const deleteResponse = await axios.delete(`${API_URL}/tests/${file.type}/delete`, {
                                                data: {
                                                    test_name: testGroup.test_name,
                                                    file_name: fileName,
                                                    file_path: filePath
                                                }
                                            });
                                            
                                            if (deleteResponse.status === 200) {
                                                messageApi.success(deleteResponse.data.message);
                                                await fetchTestGroups(); // Listeyi yenile
                                            }
                                        } catch (error: any) {
                                            const errorMessage = error.response?.data?.detail || error.message;
                                            console.error(`${fileName} silinirken hata:`, errorMessage);
                                            messageApi.error(`${fileName} silinirken bir hata oluştu: ${errorMessage}`);
                                        }
                                    }
                                }
                            }
                            await fetchTestGroups(); // Listeyi yenile
                            setSelectedFiles([]); // Seçimleri temizle
                            resolve(true);
                        } catch (error) {
                            console.error('Dosya silme hatası:', error);
                            messageApi.error('Dosyalar silinirken bir hata oluştu');
                            resolve(false);
                        }
                    },
                    onCancel() {
                        resolve(false);
                    }
                });
            });
        } catch (error) {
            console.error('Silme onayı hatası:', error);
            messageApi.error('Silme işlemi başlatılırken bir hata oluştu');
        }
    };

    const handleDeleteDirectory = async (dirName: string) => {
        try {
            await new Promise<boolean>((resolve) => {
                modal.confirm({
                    title: 'Klasör Silme Onayı',
                    content: `"${dirName}" klasörünü ve tüm içeriğini silmek istediğinize emin misiniz?`,
                    okText: 'Evet',
                    cancelText: 'İptal',
                    async onOk() {
                        try {
                            const response = await axios.delete(`${API_URL}/tests/directory/${dirName}`);
                            messageApi.success(response.data.message);
                            await fetchDirectories();
                            await fetchTestGroups();
                            resolve(true);
                        } catch (error: any) {
                            const errorMessage = error.response?.data?.detail || error.message;
                            messageApi.error(`Klasör silinirken bir hata oluştu: ${errorMessage}`);
                            resolve(false);
                        }
                    },
                    onCancel() {
                        resolve(false);
                    }
                });
            });
        } catch (error) {
            console.error('Klasör silme hatası:', error);
            messageApi.error('Klasör silme işlemi başlatılırken bir hata oluştu');
        }
    };

    useEffect(() => {
        fetchTestGroups();
        fetchDirectories();
    }, []);

    const columns: TableProps<JsonFile>['columns'] = [
        {
            title: 'Dosya Adı',
            dataIndex: 'name',
            key: 'name'
        },
        {
            title: 'Test Açıklaması',
            key: 'description',
            render: (_, record) => (
                <Space direction="vertical" size={2} style={{ width: '100%' }}>
                    <Text strong>{record.description || 'Açıklama üretilmedi'}</Text>
                    <Space wrap size={[4, 4]}>
                        {record.scenario_type ? <Tag>{record.scenario_type}</Tag> : null}
                        {record.expected_result ? (
                            <Tag color={EXPECTED_RESULT_COLORS[record.expected_result] || 'default'}>
                                {record.expected_result}
                            </Tag>
                        ) : null}
                    </Space>
                    {record.expected_message ? (
                        <Text type="secondary">{record.expected_message}</Text>
                    ) : null}
                </Space>
            )
        },
        {
            title: 'Tür',
            dataIndex: 'type',
            key: 'type',
            render: (type: keyof typeof TYPE_COLORS) => (
                <Tag color={TYPE_COLORS[type]}>{TYPE_LABELS[type]}</Tag>
            ),
            filters: Object.entries(TYPE_LABELS).map(([key, label]) => ({
                text: label,
                value: key
            })),
            onFilter: (value, record) => record.type === value
        },
        {
            title: 'Oluşturma Tarihi',
            dataIndex: 'created_at',
            key: 'created_at',
            sorter: (a, b) => a.created_at.localeCompare(b.created_at)
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
                    <Tooltip title="İndir">
                        <Button 
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownload(record)}
                        />
                    </Tooltip>
                    <Tooltip title="Sil">
                        <Button 
                            danger 
                            icon={<DeleteOutlined />}
                            onClick={() => handleDelete([record.name])}
                        />
                    </Tooltip>
                </Space>
            )
        }
    ];

    const filteredData = testGroups.filter(group => 
        group.test_name.toLowerCase().includes(searchText.toLowerCase()) ||
        group.files.some(file => 
            file.name.toLowerCase().includes(searchText.toLowerCase()) ||
            (file.description || '').toLowerCase().includes(searchText.toLowerCase()) ||
            (file.expected_message || '').toLowerCase().includes(searchText.toLowerCase())
        )
    );

    // Collapse items'ları oluştur
    const collapseItems = filteredData.map(group => ({
        key: group.test_name,
        label: (
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                <Space>
                    <strong>{group.test_name}</strong>
                    <Tag>{group.files.length} dosya</Tag>
                    <Tag>{new Date(group.created_at).toLocaleString()}</Tag>
                </Space>
                <Button 
                    danger 
                    icon={<DeleteOutlined />}
                    onClick={(e) => {
                        e.stopPropagation(); // Collapse açılmasını engelle
                        handleDeleteDirectory(group.test_name);
                    }}
                >
                    Klasörü Sil
                </Button>
            </Space>
        ),
        children: (
            <Table
                rowSelection={{
                    type: 'checkbox',
                    selectedRowKeys: selectedFiles,
                    onChange: (selectedRowKeys) => {
                        setSelectedFiles(selectedRowKeys as string[]);
                    }
                }}
                columns={columns}
                dataSource={group.files}
                rowKey="name"
                size="middle"
                pagination={{ pageSize: 10, showSizeChanger: false }}
            />
        )
    }));

    return (
        <App>
            {messageContextHolder}
            {modalContextHolder}
            <div style={{ padding: '24px' }}>
                <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <Card title="Test Sonuçları">
                        <Space direction="vertical" style={{ width: '100%' }} size="large">
                            <Space style={{ justifyContent: 'space-between', width: '100%' }}>
                                <Space>
                                    <Search
                                        placeholder="Test adı veya dosya adı ile ara..."
                                        onSearch={handleSearch}
                                        style={{ width: 300 }}
                                        allowClear
                                    />
                                    <Button 
                                        type="primary"
                                        icon={<SyncOutlined />}
                                        onClick={() => {
                                            fetchTestGroups();
                                            fetchDirectories();
                                        }}
                                        loading={loading}
                                    >
                                        Yenile
                                    </Button>
                                </Space>
                                {selectedFiles.length > 0 && (
                                    <Space>
                                        <Button 
                                            danger 
                                            icon={<DeleteOutlined />}
                                            onClick={() => handleDelete(selectedFiles)}
                                        >
                                            Seçilenleri Sil
                                        </Button>
                                    </Space>
                                )}
                            </Space>

                            <Collapse items={collapseItems} />
                        </Space>
                    </Card>
                </Space>

                <Modal
                    title="JSON Görüntüleyici"
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
                        {selectedJson}
                    </pre>
                </Modal>
            </div>
        </App>
    );
}; 
