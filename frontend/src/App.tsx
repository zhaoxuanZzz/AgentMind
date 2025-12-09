import { useState, useEffect } from 'react'
import ChatPage from './pages/ChatPage'
import KnowledgePage from './pages/KnowledgePage'
import { Layout, Menu, ConfigProvider, theme, Button, Tooltip } from 'antd'
import { BookOutlined, MessageOutlined, BulbOutlined, BulbFilled } from '@ant-design/icons'
import './App.css'

const { Header, Content } = Layout

type PageKey = 'chat' | 'knowledge'

function App() {
  const [currentPage, setCurrentPage] = useState<PageKey>('chat')
  const [isDarkMode, setIsDarkMode] = useState(true)

  useEffect(() => {
    // Initialize theme attribute
    document.documentElement.setAttribute('data-theme', isDarkMode ? 'dark' : 'light')
  }, [isDarkMode])

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode)
  }

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
    <ConfigProvider
      theme={{
        algorithm: isDarkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
        token: {
          colorPrimary: isDarkMode ? '#00F0FF' : '#1677ff',
          colorBgContainer: isDarkMode ? '#141414' : '#ffffff',
        },
        components: {
          Layout: {
            headerBg: 'transparent',
            bodyBg: 'transparent',
          },
          Menu: {
            darkItemBg: 'transparent',
            itemBg: 'transparent',
            activeBarBorderWidth: 0,
          },
        },
      }}
    >
      <Layout style={{ height: '100vh', background: 'var(--agent-bg-gradient)' }}>
        <Header style={{ 
          display: 'flex', 
          alignItems: 'center',
          background: 'var(--agent-header-bg)',
          backdropFilter: 'blur(20px)',
          borderBottom: '1px solid var(--agent-border-color)',
          padding: '0 24px',
          position: 'relative',
          zIndex: 100,
          transition: 'all 0.3s'
        }}>
          <div 
            style={{ 
              fontSize: '20px', 
              fontWeight: 'bold', 
              background: isDarkMode 
                ? 'linear-gradient(90deg, #F8FAFC 0%, #00F0FF 100%)' 
                : 'linear-gradient(90deg, #0f172a 0%, #1677ff 60%, #722ed1 100%)',
              marginRight: '40px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              transition: 'background 0.3s ease'
            }}
            className="agent-logo"
          >
            Agent System
          </div>
          <Menu
            theme={isDarkMode ? 'dark' : 'light'}
            mode="horizontal"
            selectedKeys={[currentPage]}
            items={menuItems}
            onClick={({ key }) => setCurrentPage(key as PageKey)}
            style={{ 
              flex: 1, 
              background: 'transparent',
              border: 'none',
              lineHeight: '64px'
            }}
          />
          <Tooltip title={isDarkMode ? "切换到亮色模式" : "切换到暗色模式"}>
            <Button 
              type="text" 
              icon={isDarkMode ? <BulbFilled style={{ color: '#faad14' }} /> : <BulbOutlined />} 
              onClick={toggleTheme}
              style={{ color: 'var(--agent-text-color)' }}
            />
          </Tooltip>
        </Header>
        <Content style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {currentPage === 'chat' && <ChatPage />}
          {currentPage === 'knowledge' && <KnowledgePage />}
        </Content>
      </Layout>
    </ConfigProvider>
  )
}

export default App
