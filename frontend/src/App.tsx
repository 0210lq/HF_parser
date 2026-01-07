/**
 * HF Parser 前端应用入口
 *
 * 技术栈：
 * - React 19 + TypeScript
 * - React Router v7 - 路由管理
 * - TanStack Query (React Query) - 服务端状态管理
 * - TailwindCSS - 样式框架
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Layout } from './components/layout/Layout'
import { Dashboard } from './pages/Dashboard'
import { Search } from './pages/Search'
import { Compare } from './pages/Compare'
import './index.css'

/**
 * React Query 客户端配置
 * - staleTime: 数据新鲜时间，5分钟内不会重新请求
 * - retry: 请求失败重试次数
 */
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

/**
 * 应用根组件
 *
 * 路由结构：
 * - / : 数据总览页面 (Dashboard)
 * - /search : 产品搜索页面 (Search)
 * - /compare : 产品对比页面 (Compare)
 */
function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<Search />} />
            <Route path="/compare" element={<Compare />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
