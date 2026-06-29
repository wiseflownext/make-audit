import { Routes, Route, NavLink, useLocation } from 'react-router-dom'
import UploadPage from './pages/UploadPage'
import DownloadPage from './pages/DownloadPage'
import TemplatesPage from './pages/TemplatesPage'
import TemplatePreviewPage from './pages/TemplatePreviewPage'
import './App.css'

export default function App() {
  const { pathname } = useLocation()
  const isStandalonePreview = pathname.startsWith('/preview/')

  return (
    <div className={`app${isStandalonePreview ? ' app-preview-only' : ''}`}>
      {!isStandalonePreview && (
        <nav className="app-nav">
          <NavLink to="/">上传资料</NavLink>
          <NavLink to="/download">下载资料包</NavLink>
          <NavLink to="/templates">模版管理</NavLink>
        </nav>
      )}
      <main className={`app-main${isStandalonePreview ? ' app-main-flush' : ''}`}>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/download" element={<DownloadPage />} />
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/preview/:templateId" element={<TemplatePreviewPage />} />
        </Routes>
      </main>
    </div>
  )
}
