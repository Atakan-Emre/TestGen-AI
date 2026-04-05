import React from 'react';
import { Layout, Menu } from 'antd';
import { Link, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  FileOutlined,
  ExperimentOutlined,
  AppstoreOutlined,
  FolderOutlined
} from '@ant-design/icons';

const { Header, Content, Sider } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">Ana Sayfa</Link>,
    },
    {
      key: 'files',
      icon: <FileOutlined />,
      label: 'Dosyalar',
      children: [
        {
          key: '/files/csv',
          label: <Link to="/files/csv">CSV Dosyaları</Link>,
        },
        {
          key: '/files/json',
          label: <Link to="/files/json">JSON Dosyaları</Link>,
        },
        {
          key: '/files/variables',
          label: <Link to="/files/variables">Değişken Değerleri</Link>,
        }
      ],
    },
    {
      key: 'scenarios',
      icon: <AppstoreOutlined />,
      label: 'Senaryolar',
      children: [
        {
          key: '/scenarios/create',
          label: <Link to="/scenarios/create">Senaryo Oluştur</Link>,
        },
        {
          key: '/scenarios/list',
          label: <Link to="/scenarios/list">Senaryo Listesi</Link>,
        },
      ],
    },
    {
      key: 'tests',
      icon: <ExperimentOutlined />,
      label: 'Test İşlemleri',
      children: [
        {
          key: '/tests/create',
          label: <Link to="/tests/create">Test Oluştur</Link>,
        },
        {
          key: '/tests/list',
          label: <Link to="/tests/list">Testler</Link>,
        },
      ],
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ padding: 0, background: '#fff' }}>
        <div style={{ padding: '0 24px' }}>
          <h1>TestGen AI</h1>
        </div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            defaultOpenKeys={['files', 'scenarios']}
            style={{ height: '100%', borderRight: 0 }}
            items={menuItems}
          />
        </Sider>
        <Layout style={{ padding: '24px' }}>
          <Content style={{ background: '#fff', padding: 24, margin: 0, minHeight: 280 }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
}; 
