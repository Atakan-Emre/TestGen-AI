import React from 'react';
import { Card, Tag, Button, Space, Typography, Spin, App } from 'antd';
import { FileTextOutlined, DownloadOutlined } from '@ant-design/icons';
import { BusinessRule } from '../api/services/businessRules';

const { Title, Text } = Typography;

interface BusinessRulePreviewProps {
  rule: BusinessRule | null;
  loading?: boolean;
  onDownload?: () => void;
}

export const BusinessRulePreview: React.FC<BusinessRulePreviewProps> = ({
  rule,
  loading = false,
  onDownload
}) => {
  if (loading) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <div style={{ marginTop: '16px' }}>İş kuralı yükleniyor...</div>
        </div>
      </Card>
    );
  }

  if (!rule) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '50px', color: '#999' }}>
          <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
          <div>Önizlemek için bir iş kuralı seçin</div>
        </div>
      </Card>
    );
  }

  return (
    <Card
      title={
        <Space>
          <FileTextOutlined />
          <span>{rule.name}</span>
          <Tag color="orange">İş Kuralı</Tag>
        </Space>
      }
      extra={
        onDownload && (
          <Button
            type="primary"
            icon={<DownloadOutlined />}
            onClick={onDownload}
          >
            İndir
          </Button>
        )
      }
    >
      <div style={{ marginBottom: '16px' }}>
        <Space direction="vertical" size="small">
          <Text type="secondary">
            Kaynak: {rule.source}
          </Text>
          <Text type="secondary">
            Oluşturulma: {new Date(rule.created_at).toLocaleString('tr-TR')}
          </Text>
          {rule.updated_at && (
            <Text type="secondary">
              Güncellenme: {new Date(rule.updated_at).toLocaleString('tr-TR')}
            </Text>
          )}
        </Space>
      </div>
      <pre
        style={{
          background: '#f5f5f5',
          padding: '16px',
          borderRadius: '4px',
          overflow: 'auto',
          maxHeight: '500px',
          fontSize: '14px',
          lineHeight: '1.6',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace'
        }}
      >
        {rule.content}
      </pre>
    </Card>
  );
};
