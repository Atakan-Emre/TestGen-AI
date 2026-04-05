import React, { useRef, useState } from 'react';
import { useScenarios } from '../hooks/useScenarios';
import { Button, Table, Space, message, Spin, Modal } from 'antd';
import { UploadOutlined, DeleteOutlined, EyeOutlined, SyncOutlined } from '@ant-design/icons';

const ScenarioManager: React.FC = () => {
  const {
    scenarios,
    selectedScenario,
    loading,
    error,
    syncScenarios,
    uploadScenario,
    deleteScenario,
    viewScenario,
  } = useScenarios();

  const [isModalVisible, setIsModalVisible] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.txt')) {
        message.error('Sadece TXT dosyaları yüklenebilir');
        return;
      }
      try {
        await uploadScenario(file);
        message.success('Senaryo başarıyla yüklendi');
      } catch (err) {
        message.error('Senaryo yüklenirken hata oluştu');
      }
    }
  };

  const handleSync = async () => {
    try {
      await syncScenarios();
      message.success('Senaryolar başarıyla senkronize edildi');
    } catch (err) {
      message.error('Senkronizasyon sırasında hata oluştu');
    }
  };

  const handleDelete = async (fileId: number) => {
    try {
      await deleteScenario(fileId);
      message.success('Senaryo başarıyla silindi');
    } catch (err) {
      message.error('Senaryo silinirken hata oluştu');
    }
  };

  const handleView = async (fileId: number) => {
    try {
      await viewScenario(fileId);
      setIsModalVisible(true);
    } catch (err) {
      message.error('Senaryo görüntülenirken hata oluştu');
    }
  };

  const columns = [
    {
      title: 'Senaryo Adı',
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
          accept=".txt"
          style={{ display: 'none' }}
        />
        <Button
          icon={<UploadOutlined />}
          onClick={() => fileInputRef.current?.click()}
        >
          Senaryo Yükle
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
          dataSource={scenarios}
          columns={columns}
          rowKey="id"
        />
      </Spin>

      <Modal
        title={selectedScenario?.name}
        open={isModalVisible}
        onCancel={() => setIsModalVisible(false)}
        width={800}
        footer={null}
      >
        {selectedScenario && (
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '10px', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
            wordWrap: 'break-word'
          }}>
            {selectedScenario.content}
          </pre>
        )}
      </Modal>
    </div>
  );
};

export default ScenarioManager; 