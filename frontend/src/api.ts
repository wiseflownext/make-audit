const API = '/api'

// ─── Shared helpers ────────────────────────────────────────────────────────

async function apiFetch(path: string, init?: RequestInit) {
  let res: Response
  try {
    res = await fetch(`${API}${path}`, init)
  } catch {
    throw new Error('无法连接后端服务，请确认后端已启动（端口 8000）')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || res.statusText)
  }
  return res
}

// ─── Types ─────────────────────────────────────────────────────────────────

export interface Employee {
  name: string
  department_name: string
  position_name: string
  hire_date: string
  gender: string
  id_no: string
  is_key_position: boolean
  is_internal_auditor: boolean
  is_regular_employee: boolean
  is_manager: boolean
  employment_status: string
}

export interface ManifestEntry {
  filename: string
  category: string
  skipped: boolean
  missing_keys: string[]
}

export interface PreviewFile {
  filename: string
  category: string
  display_name: string
}

export function previewUrl(filename: string) {
  return `${API}/generate/preview/${encodeURIComponent(filename)}`
}

export function pdfUrl(filename: string) {
  return `${API}/generate/pdf/${encodeURIComponent(filename)}`
}

export { apiFetch, API }
