import React, { useRef, useState } from 'react';
import { useJsonFiles } from '../hooks/useJsonFiles';
import { Button, Table, Space, message, Spin, Modal } from 'antd';
import { UploadOutlined, DeleteOutlined, EyeOutlined, SyncOutlined } from '@ant-design/icons';

const JsonFileManager: React.FC = () => {
  const {
    jsonFiles,
    selectedFile,
    loading,
    error,
    syncJsonFiles,
    uploadJsonFile,
    deleteJsonFile,
    viewJsonFile,
  } = useJsonFiles();

  const [isModalVisible, setIsModalVisible] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        message.error('Sadece JSON dosyaları yüklenebilir');
        return;
      }
      try {
        await uploadJsonFile(file);
        message.success('Dosya başarıyla yüklendi');
      } catch (err) {
        message.error('Dosya yüklenirken hata oluştu');
      }
    }
  };

  const handleSync = async () => {
    try {
      await syncJsonFiles();
      message.success('Dosyalar başarıyla senkronize edildi');
    } catch (err) {
      message.error('Senkronizasyon sırasında hata oluştu');
    }
  };

  const handleDelete = async (fileId: number) => {
    try {
      await deleteJsonFile(fileId);
      message.success('Dosya başarıyla silindi');
    } catch (err) {
      message.error('Dosya silinirken hata oluştu');
    }
  };

  const handleView = async (fileId: number) => {
    try {
      await viewJsonFile(fileId);
      setIsModalVisible(true);
    } catch (err) {
      message.error('Dosya görüntülenirken hata oluştu');
    }
  };

  const columns = [
    {
      title: 'Dosya Adı',
      dataIndex: 'name',
      key: 'name',
    },
    {
      title: 'Boyut',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => `${(size / 1024).toFixed(2)} KB`,
    },
    {
      title: 'Oluşturulma Tarihi',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString('tr-TR'),
    },
    {
      title: 'İşlemler',
      key: 'actions',
      render: (_: any, record: any) => (
        <Space>
          <Button
            icon={<EyeOutlined />}
            onClick={() => handleView(record.id)}
          >
            Görüntüle
          </Button>
          <Button
            icon={<DeleteOutlined />}
            danger
            onClick={() => handleDelete(record.id)}
          >
            Sil
          </Button>
        </Space>
      ),
    },
  ];

  if (error) {
    return <div style={{ color: 'red' }}>{error}</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <Space style={{ marginBottom: '20px' }}>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          accept=".json"
          style={{ display: 'none' }}
        />
        <Button
          icon={<UploadOutlined />}
          onClick={() => fileInputRef.current?.click()}
        >
          JSON Yükle
        </Button>
        <Button
          icon={<SyncOutlined />}
          onClick={handleSync}
        >
          Senkronize Et
        </Button>
      </Space>

      <Spin spinning={loading}>
        <Table
          dataSource={jsonFiles}
          columns={columns}
          rowKey="id"
        />
      </Spin>

      <Modal
        title={selectedFile?.name}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        width={800}
        footer={null}
      >
        {selectedFile && (
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word'
          }}>
            {typeof selectedFile.content === 'string'
              ? selectedFile.content
              : JSON.stringify(selectedFile.content, null, 2)}
          </pre>
        )}
      </Modal>
    </div>
  );
};

export default JsonFileManager; 
