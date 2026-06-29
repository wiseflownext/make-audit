import { useParams, Link } from 'react-router-dom'
import { API } from '../api'
import { FitPreviewFrame } from '../components/FitPreviewFrame'

/** Standalone preview page — open in a narrow window beside Cursor. */
export default function TemplatePreviewPage() {
  const { templateId } = useParams<{ templateId: string }>()
  if (!templateId) {
    return (
      <div data-testid="page-template-preview" className="preview-standalone">
        <p>未指定模版 ID</p>
        <Link to="/templates">返回模版管理</Link>
      </div>
    )
  }

  const previewUrl = `${API}/templates/${encodeURIComponent(templateId)}/preview`

  return (
    <div data-testid="page-template-preview" className="preview-standalone">
      <header className="preview-standalone-toolbar">
        <span className="preview-standalone-title">{decodeURIComponent(templateId)}</span>
        <div className="preview-standalone-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => window.location.reload()}
          >
            ↻ 刷新
          </button>
          <Link to="/templates" className="btn-secondary preview-standalone-link">
            ← 模版管理
          </Link>
        </div>
      </header>
      <FitPreviewFrame
        src={previewUrl}
        title="模版预览"
        className="preview-frame-fit-standalone"
      />
    </div>
  )
}
