import { useState, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { apiFetch, API } from '../api'
import { FitPreviewFrame } from '../components/FitPreviewFrame'

interface Template {
  id: string
  title: string
  category: string
  generation_granularity: string
  status: string
  output_naming: string
}

interface Placeholder {
  namespace: string
  key: string
}

type WorkbenchTab = 'preview' | 'edit' | 'placeholders'

function popOutPreview(templateId: string) {
  const url = `/preview/${encodeURIComponent(templateId)}`
  window.open(url, `preview-${templateId}`, 'width=920,height=1000,menubar=no,toolbar=no,location=no')
}

export default function TemplatesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [templates, setTemplates] = useState<Template[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [selectedCat, setSelectedCat] = useState<string>('')
  const [selected, setSelected] = useState<Template | null>(null)
  const [html, setHtml] = useState('')
  const [placeholders, setPlaceholders] = useState<Placeholder[]>([])
  const [malformed, setMalformed] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')
  const [validationReport, setValidationReport] = useState<any>(null)
  const [validating, setValidating] = useState(false)
  const [previewFullscreen, setPreviewFullscreen] = useState(false)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [activeTab, setActiveTab] = useState<WorkbenchTab>(
    () => (searchParams.get('tab') as WorkbenchTab) || 'preview',
  )

  const exitPreviewFullscreen = useCallback(() => setPreviewFullscreen(false), [])

  useEffect(() => {
    if (!previewFullscreen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') exitPreviewFullscreen()
    }
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
    }
  }, [previewFullscreen, exitPreviewFullscreen])

  useEffect(() => {
    apiFetch('/templates/').then(r => r.json()).then(setTemplates)
    apiFetch('/templates/categories').then(r => r.json()).then(setCategories)
  }, [])

  // Restore selection from URL on load
  useEffect(() => {
    const id = searchParams.get('id')
    if (!id || templates.length === 0) return
    const tmpl = templates.find(t => t.id === id)
    if (tmpl && selected?.id !== tmpl.id) {
      void selectTemplate(tmpl, false)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [templates])

  const filtered = selectedCat ? templates.filter(t => t.category === selectedCat) : templates

  async function selectTemplate(t: Template, syncUrl = true) {
    setSelected(t)
    setMsg('')
    setPreviewUrl(`${API}/templates/${encodeURIComponent(t.id)}/preview`)
    const [htmlRes, phRes] = await Promise.all([
      apiFetch(`/templates/${encodeURIComponent(t.id)}/html`).then(r => r.json()),
      apiFetch(`/templates/${encodeURIComponent(t.id)}/placeholders`).then(r => r.json()),
    ])
    setHtml(htmlRes.html)
    setPlaceholders(phRes.placeholders)
    setMalformed(phRes.malformed)
    if (syncUrl) {
      setSearchParams(prev => {
        const next = new URLSearchParams(prev)
        next.set('id', t.id)
        next.set('tab', activeTab)
        return next
      })
    }
  }

  function switchTab(tab: WorkbenchTab) {
    setActiveTab(tab)
    setSearchParams(prev => {
      const next = new URLSearchParams(prev)
      if (selected) next.set('id', selected.id)
      next.set('tab', tab)
      return next
    })
  }

  async function save() {
    if (!selected) return
    setSaving(true)
    try {
      await apiFetch(`/templates/${encodeURIComponent(selected.id)}/html`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ html }),
      })
      setMsg('✓ 模版已保存')
      const phRes = await apiFetch(`/templates/${encodeURIComponent(selected.id)}/placeholders`).then(r => r.json())
      setPlaceholders(phRes.placeholders)
      setMalformed(phRes.malformed)
      // Bust iframe cache after save
      setPreviewUrl(`${API}/templates/${encodeURIComponent(selected.id)}/preview?t=${Date.now()}`)
    } catch (e: any) {
      setMsg('✗ ' + e.message)
    }
    setSaving(false)
  }

  async function runValidation() {
    setValidating(true)
    try {
      const res = await apiFetch('/templates/validate/all').then(r => r.json())
      setValidationReport(res)
    } catch (e: any) {
      setMsg('✗ ' + (e as any).message)
    }
    setValidating(false)
  }

  return (
    <div
      data-testid="page-templates"
      className={`page-content templates-layout${sidebarCollapsed ? ' templates-sidebar-collapsed' : ''}`}
    >
      <aside className={`templates-sidebar${sidebarCollapsed ? ' is-collapsed' : ''}`}>
        <div className="templates-sidebar-head">
          {!sidebarCollapsed && <h2>模版管理</h2>}
          <button
            type="button"
            className="sidebar-toggle"
            onClick={() => setSidebarCollapsed(c => !c)}
            title={sidebarCollapsed ? '展开列表' : '收起列表'}
            aria-label={sidebarCollapsed ? '展开列表' : '收起列表'}
          >
            {sidebarCollapsed ? '»' : '«'}
          </button>
        </div>
        {!sidebarCollapsed && (
          <>
            <select value={selectedCat} onChange={e => setSelectedCat(e.target.value)} className="cat-select">
              <option value="">全部分类</option>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
            <ul className="tmpl-list">
              {filtered.map(t => (
                <li
                  key={t.id}
                  className={`tmpl-item ${selected?.id === t.id ? 'tmpl-active' : ''}`}
                  onClick={() => selectTemplate(t)}
                  title={t.title}
                >
                  <span className="tmpl-title">{t.title}</span>
                  <span className={`status-dot ${t.status === 'reviewed_ready' ? 'dot-green' : 'dot-yellow'}`} />
                </li>
              ))}
            </ul>
            <button onClick={runValidation} disabled={validating} className="btn-secondary tmpl-validate-btn">
              {validating ? '校验中…' : '▶ 运行全局占位符校验'}
            </button>
          </>
        )}
      </aside>

      <div className="templates-main">
        {selected ? (
          <>
            <div className="tmpl-header">
              <h2>{selected.title}</h2>
              <div className="tmpl-meta">
                <span className="chip chip-blue">{selected.generation_granularity}</span>
                <span className="chip chip-gray">输出: {selected.output_naming}</span>
              </div>
            </div>

            <div className="tmpl-workbench-tabs" role="tablist" aria-label="模版工作区">
              {([
                ['preview', '预览'],
                ['edit', 'HTML 编辑'],
                ['placeholders', `占位符（${placeholders.length}）`],
              ] as const).map(([tab, label]) => (
                <button
                  key={tab}
                  type="button"
                  role="tab"
                  aria-selected={activeTab === tab}
                  className={`tmpl-tab${activeTab === tab ? ' tmpl-tab-active' : ''}`}
                  onClick={() => switchTab(tab)}
                >
                  {label}
                </button>
              ))}
            </div>

            {activeTab === 'preview' && (
              <section className="card card-compact tmpl-preview-panel" role="tabpanel">
                <div className="editor-header">
                  <h3>预览（示例数据）</h3>
                  <div className="preview-actions">
                    <button
                      type="button"
                      onClick={() => popOutPreview(selected.id)}
                      className="btn-secondary"
                      title="在独立窗口打开，便于与 Cursor 并排"
                    >
                      ↗ 弹出预览
                    </button>
                    <button
                      type="button"
                      onClick={() => setPreviewFullscreen(true)}
                      className="btn-secondary"
                      title="全屏预览"
                    >
                      ⛶ 全屏
                    </button>
                  </div>
                </div>
                <FitPreviewFrame src={previewUrl} title="模版预览" />
              </section>
            )}

            {activeTab === 'placeholders' && (
              <section className="card card-compact" role="tabpanel">
                <h3>占位符（{placeholders.length}）</h3>
                {placeholders.length > 0 ? (
                  <div className="ph-chips">
                    {placeholders.map((p, i) => (
                      <span key={i} className="ph-chip">
                        {`{{${p.namespace}.${p.key}}}`}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="hint">此模版暂无占位符</p>
                )}
                {malformed.length > 0 && (
                  <div className="malformed-list">
                    <strong>⚠ 格式错误占位符:</strong> {malformed.join(', ')}
                  </div>
                )}
              </section>
            )}

            {activeTab === 'edit' && (
              <section className="card card-compact" role="tabpanel">
                <div className="editor-header">
                  <h3>HTML 编辑</h3>
                  <button onClick={save} disabled={saving} className="btn-primary">
                    {saving ? '保存中…' : '保存'}
                  </button>
                </div>
                {msg && <p className={msg.startsWith('✓') ? 'msg-ok' : 'msg-err'}>{msg}</p>}
                <textarea
                  className="html-editor html-editor-tall"
                  value={html}
                  onChange={e => setHtml(e.target.value)}
                  rows={20}
                  spellCheck={false}
                />
              </section>
            )}

            {previewFullscreen && (
              <div className="preview-fullscreen-overlay" role="dialog" aria-modal="true" aria-label="模版预览全屏">
                <div className="preview-fullscreen-toolbar">
                  <span>{selected.title} — 预览（示例数据）</span>
                  <button type="button" onClick={exitPreviewFullscreen} className="btn-secondary">
                    ✕ 退出全屏
                  </button>
                </div>
                <div className="preview-fullscreen-body">
                  <FitPreviewFrame src={previewUrl} title="模版预览" className="preview-frame-fit-fullscreen" />
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <p>← 从左侧列表选择一个模版进行查看或编辑</p>
            <p className="hint">提示：收起左侧列表、切换到「预览」标签，或点击「弹出预览」以便与 Cursor 并排使用</p>
          </div>
        )}

        {validationReport && (
          <section className="card">
            <h3>全局占位符校验报告</h3>
            <div className="summary-chips">
              <span className="chip chip-blue">扫描 {validationReport.templates_scanned} 个模版</span>
              <span className={`chip ${validationReport.templates_with_issues > 0 ? 'chip-yellow' : 'chip-green'}`}>
                {validationReport.templates_with_issues > 0 ? `⚠ ${validationReport.templates_with_issues} 个有问题` : '✓ 全部通过'}
              </span>
            </div>
            {validationReport.gaps?.map((g: any, i: number) => (
              <details key={i} className="gap-detail">
                <summary>[{g.template_id}] {g.template_title || ''}</summary>
                {g.unknown_namespaces?.length > 0 && <p>未知命名空间: {g.unknown_namespaces.join(', ')}</p>}
                {g.unknown_keys?.length > 0 && <p>未知字段: {g.unknown_keys.join(', ')}</p>}
                {g.malformed?.length > 0 && <p>格式错误: {g.malformed.join(', ')}</p>}
              </details>
            ))}
          </section>
        )}
      </div>
    </div>
  )
}
