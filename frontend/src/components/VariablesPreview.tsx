import React, { useState, useEffect } from 'react';
import { Card, Table, Spin, Alert, Button, Typography, Space } from 'antd';
import { EyeOutlined, EyeInvisibleOutlined } from '@ant-design/icons';
import { variablesApi } from '../api/variables';

const { Text, Title } = Typography;

interface VariablesPreviewProps {
  profileName?: string;
  maxItems?: number;
  onError?: (error: string) => void;
}

export const VariablesPreview: React.FC<VariablesPreviewProps> = ({
  profileName,
  maxItems = 10,
  onError
}) => {
  const [variables, setVariables] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showAll, setShowAll] = useState(false);

  useEffect(() => {
    if (profileName && profileName !== 'default') {
      loadProfile();
    } else {
      setVariables({});
      setError(null);
    }
  }, [profileName]);

  const loadProfile = async () => {
    if (!profileName) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const profileData = await variablesApi.fetchProfile(profileName);
      setVariables(profileData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Profil yüklenemedi';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const getDisplayVariables = () => {
    const entries = Object.entries(variables);
    return showAll ? entries : entries.slice(0, maxItems);
  };

  const columns = [
    {
      title: 'Anahtar',
      dataIndex: 'variableKey',
      key: 'variableKey',
      render: (text: string) => (
        <Text code style={{ fontSize: '12px' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Değer',
      dataIndex: 'value',
      key: 'value',
      render: (text: string) => (
        <Text style={{ fontSize: '12px' }}>
          {text}
        </Text>
      ),
    },
  ];

  const dataSource = getDisplayVariables().map(([key, value], index) => ({
    key: `${key}-${index}`,
    variableKey: key,
    value: value,
  }));

  if (!profileName || profileName === 'default') {
    return (
      <Card size="small" title="Variables Profili Önizleme">
        <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
          <Text type="secondary">Profil seçilmedi veya varsayılan profil</Text>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card size="small" title="Variables Profili Önizleme">
        <Alert
          message="Profil Yüklenemedi"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={loadProfile}>
              Tekrar Dene
            </Button>
          }
        />
      </Card>
    );
  }

  if (loading) {
    return (
      <Card size="small" title="Variables Profili Önizleme">
        <div style={{ textAlign: 'center', padding: '20px' }}>
          <Spin />
          <div style={{ marginTop: '8px' }}>
            <Text type="secondary">Profil yükleniyor...</Text>
          </div>
        </div>
      </Card>
    );
  }

  const totalVariables = Object.keys(variables).length;
  const displayCount = showAll ? totalVariables : Math.min(maxItems, totalVariables);

  return (
    <Card 
      size="small" 
      title={
        <Space>
          <span>Variables Profili Önizleme</span>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            ({displayCount}/{totalVariables} değişken)
          </Text>
        </Space>
      }
      extra={
        totalVariables > maxItems && (
          <Button
            type="link"
            size="small"
            icon={showAll ? <EyeInvisibleOutlined /> : <EyeOutlined />}
            onClick={() => setShowAll(!showAll)}
          >
            {showAll ? 'Gizle' : 'Tümünü Göster'}
          </Button>
        )
      }
    >
      {totalVariables === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '20px' }}>
          <Text type="secondary">Bu profilde değişken bulunamadı</Text>
        </div>
      ) : (
        <Table
          dataSource={dataSource}
          columns={columns}
          pagination={false}
          size="small"
          showHeader={true}
          scroll={{ y: 200 }}
          style={{ marginTop: '8px' }}
        />
      )}
    </Card>
  );
};
