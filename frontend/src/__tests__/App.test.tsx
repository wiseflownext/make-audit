import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import App from '../App'

describe('App routing skeleton', () => {
  it('renders upload page at /', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByTestId('page-upload')).toBeInTheDocument()
  })

  it('renders download page at /download', () => {
    render(
      <MemoryRouter initialEntries={['/download']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByTestId('page-download')).toBeInTheDocument()
  })

  it('renders templates page at /templates', () => {
    render(
      <MemoryRouter initialEntries={['/templates']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByTestId('page-templates')).toBeInTheDocument()
  })

  it('shows nav links on all pages', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>
    )
    expect(screen.getByRole('link', { name: /上传资料/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /下载资料包/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /模版管理/i })).toBeInTheDocument()
  })
})
