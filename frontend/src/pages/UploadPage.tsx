import { useState, useEffect } from 'react'
import { apiFetch, API } from '../api'
import type { Employee } from '../api'

function SignLinkBlock() {
  const signUrl = `${window.location.origin}/sign`
  const qrApiUrl = `https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=${encodeURIComponent(signUrl)}`

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
      <img
        src={qrApiUrl}
        alt="手机签名二维码"
        style={{ width: 100, height: 100, borderRadius: 6, border: '1px solid #bfdbfe', flexShrink: 0 }}
        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <p style={{ margin: '0 0 6px', fontSize: '0.82rem', color: '#6b7280' }}>
          手机和电脑需在同一局域网内
        </p>
        <a
          href="/sign"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            display: 'inline-block',
            padding: '8px 16px',
            background: '#2563eb',
            color: '#fff',
            borderRadius: 6,
            textDecoration: 'none',
            fontSize: '0.875rem',
            fontWeight: 600,
          }}
        >
          📱 打开手机签名页面
        </a>
        <p style={{ margin: '6px 0 0', fontSize: '0.78rem', color: '#9ca3af', wordBreak: 'break-all' }}>
          {signUrl}
        </p>
      </div>
    </div>
  )
}

type EnterpriseInfo = {
  name: string
  short_name?: string
  legal_rep?: string
  contact?: string
  phone?: string
  address?: string
  year?: string
}

function fileFromDataTransfer(dt: DataTransfer): File | null {
  if (dt.files?.length) return dt.files[0]
  for (const item of dt.items) {
    if (item.kind === 'file') {
      const f = item.getAsFile()
      if (f) return f
    }
  }
  return null
}

// ─── Combined intake upload ───────────────────────────────────────────────

function IntakeUpload({
  onUploaded,
}: {
  onUploaded: (data: { enterprise: EnterpriseInfo; employees: Employee[] }) => void
}) {
  const [enterprise, setEnterprise] = useState<EnterpriseInfo | null>(null)
  const [employeeCount, setEmployeeCount] = useState(0)
  const [uploading, setUploading] = useState(false)
  const [msg, setMsg] = useState('')

  useEffect(() => {
    const prevent = (e: DragEvent) => e.preventDefault()
    window.addEventListener('dragover', prevent)
    window.addEventListener('drop', prevent)
    return () => {
      window.removeEventListener('dragover', prevent)
      window.removeEventListener('drop', prevent)
    }
  }, [])

  useEffect(() => {
    Promise.all([
      apiFetch('/intake/enterprise').then(r => r.json()),
      apiFetch('/intake/roster').then(r => r.json()),
    ]).then(([ent, roster]) => {
      if (ent.name) {
        setEnterprise(ent)
        if (roster.count > 0) {
          setEmployeeCount(roster.count)
          onUploaded({ enterprise: ent, employees: roster.employees })
        }
      }
    })
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function downloadTemplate() {
    setMsg('')
    try {
      const res = await fetch(`${API}/intake/template`)
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }))
        throw new Error(err.detail || res.statusText)
      }
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      Object.assign(document.createElement('a'), { href: url, download: '审核资料上传模板.xlsx' }).click()
      URL.revokeObjectURL(url)
    } catch (e: any) {
      setMsg('✗ 模板下载失败: ' + e.message)
    }
  }

  const [dragging, setDragging] = useState(false)

  async function processFile(file: File) {
    setUploading(true)
    setMsg('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const res = await apiFetch('/intake/upload', { method: 'POST', body: fd })
      const data = await res.json()
      setEnterprise(data.enterprise)
      setEmployeeCount(data.count)
      setMsg(`✓ 已解析企业「${data.enterprise.name}」及 ${data.count} 名员工`)
      onUploaded({ enterprise: data.enterprise, employees: data.employees })
    } catch (e: any) { setMsg('✗ ' + e.message) }
    setUploading(false)
  }

  function handleFile(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) void processFile(file)
    e.target.value = ''
  }

  return (
    <section className="card">
      <h2>① 企业资料与花名册</h2>
      <p className="hint">下载模板后在同一 Excel 文件中填写「企业基础资料」与「人员花名册」两个工作表，然后上传。</p>
      <div className="row-actions">
        <button onClick={downloadTemplate} className="btn-secondary">↓ 下载上传模板</button>
        <label className="btn-primary" style={{ cursor: 'pointer' }}>
          {uploading ? '解析中…' : '上传资料 (Excel)'}
          <input type="file" accept=".xlsx,.xls,.xlsm" onChange={handleFile} style={{ display: 'none' }} />
        </label>
      </div>
      <div
        className={`drop-zone${dragging ? ' drop-zone-active' : ''}`}
        onDragEnter={e => { e.preventDefault(); setDragging(true) }}
        onDragOver={e => e.preventDefault()}
        onDragLeave={e => { if (e.currentTarget === e.target) setDragging(false) }}
        onDrop={e => {
          e.preventDefault()
          e.stopPropagation()
          setDragging(false)
          const file = fileFromDataTransfer(e.dataTransfer)
          if (file) void processFile(file)
          else setMsg('✗ 未能读取拖拽的文件，请重试或点击按钮选择文件')
        }}
      >
        <span className="drop-zone-icon">📄</span>
        <span>{uploading ? '解析中…' : '或将 Excel 文件拖拽到此处'}</span>
      </div>
      {enterprise && (
        <div className="hint" style={{ marginTop: '0.75rem' }}>
          已上传：{enterprise.name}
          {enterprise.short_name ? `（${enterprise.short_name}）` : ''}
          {enterprise.year ? ` · ${enterprise.year} 年度` : ''}
          {employeeCount > 0 ? ` · ${employeeCount} 名员工` : ''}
        </div>
      )}
      {msg && <p className={msg.startsWith('✓') ? 'msg-ok' : 'msg-err'}>{msg}</p>}
    </section>
  )
}

// ─── Employee table ───────────────────────────────────────────────────────

function EmployeeTable({ employees }: { employees: Employee[] }) {
  if (!employees.length) return null
  return (
    <section className="card">
      <h2>员工列表（{employees.length} 人）</h2>
      <div style={{ overflowX: 'auto' }}>
        <table className="data-table">
          <thead>
            <tr>{['姓名', '部门', '岗位', '入职日期', '性别', '重点岗位', '内审员', '普通员工'].map(h => <th key={h}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {employees.map((e, i) => (
              <tr key={i}>
                <td>{e.name}</td><td>{e.department_name}</td><td>{e.position_name}</td>
                <td>{e.hire_date}</td><td>{e.gender}</td>
                <td>{e.is_key_position ? '是' : '否'}</td>
                <td>{e.is_internal_auditor ? '是' : '否'}</td>
                <td>{e.is_regular_employee ? '是' : '否'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

// ─── Signature upload ────────────────────────────────────────────────────

function SignatureUpload({ employees }: { employees: Employee[] }) {
  const [uploaded, setUploaded] = useState<string[]>([])
  const [msg, setMsg] = useState('')
  const [dragOver, setDragOver] = useState<string | null>(null)

  async function processFile(name: string, file: File) {
    const fd = new FormData()
    fd.append('file', file)
    try {
      await apiFetch(`/signatures/upload/${encodeURIComponent(name)}`, { method: 'POST', body: fd })
      setUploaded(u => [...u.filter(n => n !== name), name])
      setMsg(`✓ 已上传 ${name} 的签名`)
    } catch (ex: any) { setMsg('✗ ' + ex.message) }
  }

  function handleFile(name: string, e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) void processFile(name, file)
    e.target.value = ''
  }

  if (!employees.length) return null

  return (
    <section className="card">
      <h2>② 可选：员工签名照片（抠底处理）</h2>
      <p className="hint">未上传的员工将使用手写体文字签名代替，不影响生成。可将图片拖拽到对应员工区域上传。</p>
      <div className="sig-grid">
        {employees.slice(0, 20).map(e => (
          <label
            key={e.name}
            className={`sig-item ${uploaded.includes(e.name) ? 'sig-done' : ''}${dragOver === e.name ? ' sig-item-dragover' : ''}`}
            onDragEnter={ev => { ev.preventDefault(); setDragOver(e.name) }}
            onDragOver={ev => ev.preventDefault()}
            onDragLeave={ev => { if (ev.currentTarget === ev.target) setDragOver(null) }}
            onDrop={ev => {
              ev.preventDefault()
              ev.stopPropagation()
              setDragOver(null)
              const file = fileFromDataTransfer(ev.dataTransfer)
              if (file) void processFile(e.name, file)
            }}
          >
            <span>{e.name}</span>
            <span className="sig-status">{uploaded.includes(e.name) ? '✓ 已上传' : '点击或拖拽上传'}</span>
            <input type="file" accept="image/*" onChange={ev => handleFile(e.name, ev)} style={{ display: 'none' }} />
          </label>
        ))}
        {employees.length > 20 && <span className="hint">…及其余 {employees.length - 20} 人</span>}
      </div>
      {msg && <p className={msg.startsWith('✓') ? 'msg-ok' : 'msg-err'}>{msg}</p>}
    </section>
  )
}

// ─── Main page ────────────────────────────────────────────────────────────

export default function UploadPage() {
  const [employees, setEmployees] = useState<Employee[]>([])
  const [ready, setReady] = useState(false)

  return (
    <div data-testid="page-upload" className="page-content">
      <h1 className="page-title">上传资料</h1>
      <IntakeUpload onUploaded={({ employees: rows }) => {
        setEmployees(rows)
        setReady(true)
      }} />
      <EmployeeTable employees={employees} />
      <SignatureUpload employees={employees} />
      {ready && employees.length > 0 && (
        <section className="card card-action">
          <p>企业资料与花名册均已就绪，可前往 <strong>下载资料包</strong> 页面触发生成。</p>
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#eff6ff', borderRadius: 8, border: '1px solid #bfdbfe' }}>
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: '#1e40af', fontWeight: 500 }}>
              📱 手机签名收集
            </p>
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.85rem', color: '#3b82f6' }}>
              用手机扫描二维码或访问以下链接，让员工直接在手机上手写签名：
            </p>
            <SignLinkBlock />
          </div>
        </section>
      )}
    </div>
  )
}
