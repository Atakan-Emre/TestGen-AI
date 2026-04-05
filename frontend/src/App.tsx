import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Layout, Menu, Typography, App as AntApp, Spin, Tag } from 'antd';
import { 
  HomeOutlined, 
  FileTextOutlined, 
  FileExcelOutlined, 
  CodeOutlined,
  ExperimentOutlined,
  AppstoreOutlined
} from '@ant-design/icons';
import { IS_DEMO_MODE } from './config';

const { Header, Content, Sider } = Layout;
const { Title } = Typography;

const HomePage = lazy(() =>
  import('./pages/Home/HomePage').then((module) => ({ default: module.HomePage }))
);
const CsvFilesPage = lazy(() =>
  import('./pages/Files/CsvFilesPage').then((module) => ({ default: module.CsvFilesPage }))
);
const JsonFilesPage = lazy(() =>
  import('./pages/Files/JsonFilesPage').then((module) => ({ default: module.JsonFilesPage }))
);
const VariablesPage = lazy(() =>
  import('./pages/Files/VariablesPage').then((module) => ({ default: module.VariablesPage }))
);
const ScenarioCreatePage = lazy(() =>
  import('./pages/Scenarios/ScenarioCreatePage').then((module) => ({ default: module.ScenarioCreatePage }))
);
const ScenarioListPage = lazy(() =>
  import('./pages/Scenarios/ScenarioListPage').then((module) => ({ default: module.ScenarioListPage }))
);
const TestCreatePage = lazy(() => import('./pages/Tests/TestCreatePage'));
const TestListPage = lazy(() =>
  import('./pages/Tests/TestListPage').then((module) => ({ default: module.TestListPage }))
);

const App: React.FC = () => {
  const routerBaseName =
    import.meta.env.BASE_URL && import.meta.env.BASE_URL !== '/'
      ? import.meta.env.BASE_URL.replace(/\/$/, '')
      : undefined;

  const menuItems = [
    {
        key: '1',
        icon: <HomeOutlined />,
        label: <Link to="/">Ana Sayfa</Link>
    },
    {
        key: 'sub1',
        icon: <FileTextOutlined />,
        label: 'Dosyalar',
        children: [
            {
                key: '2',
                icon: <FileExcelOutlined />,
                label: <Link to="/files/csv">CSV Dosyaları</Link>
            },
            {
                key: '3',
                icon: <CodeOutlined />,
                label: <Link to="/files/json">JSON Dosyaları</Link>
            },
            {
                key: '4',
                icon: <FileTextOutlined />,
                label: <Link to="/files/variables">Değişken Değerleri</Link>
            }
        ]
    },
    {
        key: 'sub2',
        icon: <FileTextOutlined />,
        label: 'Senaryolar',
        children: [
            {
                key: '5',
                label: <Link to="/scenarios/create">Senaryo Oluştur</Link>
            },
            {
                key: '6',
                label: <Link to="/scenarios/list">Senaryo Listesi</Link>
            }
        ]
    },
    {
        key: 'sub3',
        icon: <ExperimentOutlined />,
        label: 'Testler',
        children: [
            {
                key: '7',
                label: <Link to="/tests/create">Test Oluştur</Link>
            },
            {
                key: '8',
                label: <Link to="/tests/list">Test Listesi</Link>
            }
        ]
    }
  ];

  return (
    <AntApp>
      <Router basename={routerBaseName}>
        <Layout className="app-layout">
          <Header className="app-header">
            <div className="header-title">
              <AppstoreOutlined className="header-icon" />
              <Title level={4}>TestGen AI</Title>
              {IS_DEMO_MODE ? <Tag color="gold">Demo</Tag> : null}
            </div>
          </Header>
          <Layout>
            <Sider width={200} className="app-sider">
              <Menu
                mode="inline"
                defaultSelectedKeys={['1']}
                className="app-menu"
                items={menuItems}
              />
            </Sider>
            <Layout>
              <Content className="app-content">
                <Suspense
                  fallback={
                    <div style={{ minHeight: '40vh', display: 'grid', placeItems: 'center' }}>
                      <Spin size="large" />
                    </div>
                  }
                >
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/files/csv" element={<CsvFilesPage />} />
                    <Route path="/files/json" element={<JsonFilesPage />} />
                    <Route path="/files/variables" element={<VariablesPage />} />
                    <Route path="/scenarios/create" element={<ScenarioCreatePage />} />
                    <Route path="/scenarios/list" element={<ScenarioListPage />} />
                    <Route path="/tests/create" element={<TestCreatePage />} />
                    <Route path="/tests/list" element={<TestListPage />} />
                  </Routes>
                </Suspense>
              </Content>
            </Layout>
          </Layout>
        </Layout>
      </Router>
    </AntApp>
  );
};

export default App; 
