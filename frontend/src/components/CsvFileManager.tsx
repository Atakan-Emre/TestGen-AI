import React, { useRef } from 'react';
import { useCsvFiles } from '../hooks/useCsvFiles';
import { Button, Table, Space, Upload, message, Spin } from 'antd';
import { UploadOutlined, DeleteOutlined, EyeOutlined, SyncOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';

const CsvFileManager: React.FC = () => {
  const {
    csvFiles,
    selectedFile,
    loading,
    error,
    syncCsvFiles,
    uploadCsvFile,
    deleteCsvFile,
    viewCsvFile,
  } = useCsvFiles();

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.csv')) {
        message.error('Sadece CSV dosyaları yüklenebilir');
        return;
      }
      try {
        await uploadCsvFile(file);
        message.success('Dosya başarıyla yüklendi');
      } catch (err) {
        message.error('Dosya yüklenirken hata oluştu');
      }
    }
  };

  const handleSync = async () => {
    try {
      await syncCsvFiles();
      message.success('Dosyalar başarıyla senkronize edildi');
    } catch (err) {
      message.error('Senkronizasyon sırasında hata oluştu');
    }
  };

  const handleDelete = async (fileId: number) => {
    try {
      await deleteCsvFile(fileId);
      message.success('Dosya başarıyla silindi');
    } catch (err) {
      message.error('Dosya silinirken hata oluştu');
    }
  };

  const handleView = async (fileId: number) => {
    try {
      await viewCsvFile(fileId);
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
          accept=".csv"
          style={{ display: 'none' }}
        />
        <Button
          icon={<UploadOutlined />}
          onClick={() => fileInputRef.current?.click()}
        >
          CSV Yükle
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
          dataSource={csvFiles}
          columns={columns}
          rowKey="id"
        />
      </Spin>

      {selectedFile && (
        <div style={{ marginTop: '20px' }}>
          <h3>Seçili Dosya İçeriği:</h3>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            {selectedFile.content}
          </pre>
        </div>
      )}
    </div>
  );
};

export default CsvFileManager; 