import React, { useState, useEffect } from 'react';
import { Select, Spin, Alert, Button } from 'antd';
import { ReloadOutlined } from '@ant-design/icons';
import { variablesApi } from '../api/variables';
import { VariableProfileInfo } from '../types/variables';

const { Option } = Select;

interface VariablesProfileSelectProps {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  disabled?: boolean;
  onError?: (error: string) => void;
}

export const VariablesProfileSelect: React.FC<VariablesProfileSelectProps> = ({
  value,
  onChange,
  placeholder = "(default)",
  disabled = false,
  onError
}) => {
  const [profiles, setProfiles] = useState<VariableProfileInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadProfiles = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const profilesData = await variablesApi.fetchProfiles();
      setProfiles(profilesData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Profil listesi yüklenemedi';
      setError(errorMessage);
      onError?.(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const handleRefresh = () => {
    loadProfiles();
  };

  const getFormatBadge = (format: string) => {
    const formatColors: Record<string, string> = {
      'txt': '#52c41a',
      'json': '#1890ff',
      'yaml': '#722ed1'
    };
    
    return (
      <span 
        style={{ 
          fontSize: '10px', 
          padding: '2px 6px', 
          borderRadius: '4px', 
          backgroundColor: formatColors[format] || '#d9d9d9',
          color: 'white',
          marginLeft: '4px'
        }}
      >
        {format.toUpperCase()}
      </span>
    );
  };

  if (error) {
    return (
      <div>
        <Alert
          message="Profil Listesi Yüklenemedi"
          description={error}
          type="error"
          showIcon
          action={
            <Button size="small" onClick={handleRefresh} icon={<ReloadOutlined />}>
              Tekrar Dene
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      disabled={disabled}
      loading={loading}
      style={{ width: '100%' }}
      aria-label="Variables Profili"
      suffixIcon={loading ? <Spin size="small" /> : undefined}
      dropdownRender={(menu) => (
        <div>
          {menu}
          <div style={{ padding: '8px', borderTop: '1px solid #f0f0f0' }}>
            <Button 
              type="link" 
              size="small" 
              icon={<ReloadOutlined />} 
              onClick={handleRefresh}
              style={{ width: '100%' }}
            >
              Yenile
            </Button>
          </div>
        </div>
      )}
    >
      <Option value="default">
        <span>default</span>
        <span style={{ color: '#999', marginLeft: '8px' }}>(varsayılan)</span>
      </Option>
      {profiles.map((profile) => (
        <Option key={profile.name} value={profile.name}>
          <span>{profile.name}</span>
          {getFormatBadge(profile.format)}
          {profile.sizeBytes && (
            <span style={{ color: '#999', marginLeft: '8px', fontSize: '11px' }}>
              ({Math.round(profile.sizeBytes / 1024)}KB)
            </span>
          )}
        </Option>
      ))}
    </Select>
  );
};
