import { useState, Suspense, lazy } from 'react'
import { Layout, Menu, ConfigProvider, Spin, App as AntApp } from 'antd'
import { BookOutlined, MessageOutlined } from '@ant-design/icons'
import { ErrorBoundary } from './components/ErrorBoundary'
import { useErrorHandler } from './hooks/useErrorHandler'
import './App.css'

// 懒加载页面组件
const ChatPage = lazy(() => import('./pages/ChatPage'))
const KnowledgePage = lazy(() => import('./pages/KnowledgePage'))

const { Header, Content } = Layout

type PageKey = 'chat' | 'knowledge'

function AppContent() {
  const [currentPage, setCurrentPage] = useState<PageKey>('chat')
  
  // 注册全局错误处理 hook (必须在 AntApp 上下文中)
  useErrorHandler()

  const menuItems = [
    {
      key: 'chat',
      icon: <MessageOutlined />,
      label: '智能对话',
    },
    {
      key: 'knowledge',
      icon: <BookOutlined />,
      label: '知识库管理',
    },
  ]

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center',
        borderBottom: '1px solid #e8e8e8',
        padding: '0 24px',
        position: 'relative',
        zIndex: 100,
      }}>
        <div 
          style={{ 
            fontSize: '20px', 
            fontWeight: 'bold', 
            background: 'linear-gradient(90deg, #1677ff 0%, #722ed1 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginRight: '40px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
          }}
        >
          Agent System
        </div>
        <Menu
          mode="horizontal"
          selectedKeys={[currentPage]}
          items={menuItems}
          onClick={({ key }) => setCurrentPage(key as PageKey)}
          style={{ 
            flex: 1, 
            border: 'none',
            lineHeight: '64px'
          }}
        />
      </Header>
      <Content style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <ErrorBoundary>
          <Suspense 
            fallback={
              <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <Spin size="large" spinning tip="加载模块中..." />
              </div>
            }
          >
            {currentPage === 'chat' && <ChatPage />}
            {currentPage === 'knowledge' && <KnowledgePage />}
          </Suspense>
        </ErrorBoundary>
      </Content>
    </Layout>
  )
}

function App() {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1677ff',
          colorBgContainer: '#ffffff',
          colorBgLayout: '#ffffff',
          borderRadius: 8,
          colorBorder: '#e8e8e8',
        },
        components: {
          Layout: {
            headerBg: '#ffffff',
            bodyBg: '#ffffff',
          },
        },
      }}
    >
      <AntApp>
        <AppContent />
      </AntApp>
    </ConfigProvider>
  )
}

export default App
