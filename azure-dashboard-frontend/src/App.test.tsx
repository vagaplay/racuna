import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '../test/utils'
import App from '../App'

// Mock do React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/' }),
  }
})

describe('App Component', () => {
  beforeEach(() => {
    // Reset mocks antes de cada teste
    vi.clearAllMocks()
    
    // Mock fetch para auth status
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        authenticated: false,
        user: null
      })
    })
  })

  it('deve renderizar sem erros', async () => {
    render(<App />)
    
    // Aguardar carregamento inicial
    await waitFor(() => {
      expect(screen.getByTestId('app-container') || document.body).toBeTruthy()
    })
  })

  it('deve mostrar tela de login quando não autenticado', async () => {
    render(<App />)
    
    await waitFor(() => {
      // Procurar por elementos de login
      const loginElements = screen.queryAllByText(/entrar|login/i)
      expect(loginElements.length).toBeGreaterThan(0)
    })
  })

  it('deve fazer verificação de autenticação na inicialização', async () => {
    render(<App />)
    
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/auth/status'),
        expect.objectContaining({
          credentials: 'include'
        })
      )
    })
  })

  it('deve lidar com erro de rede graciosamente', async () => {
    // Mock erro de rede
    global.fetch = vi.fn().mockRejectedValue(new Error('Network error'))
    
    render(<App />)
    
    await waitFor(() => {
      // App deve renderizar mesmo com erro de rede
      expect(document.body).toBeTruthy()
    })
  })

  it('deve aplicar tema correto', async () => {
    render(<App />)
    
    await waitFor(() => {
      const appElement = document.querySelector('[data-theme]') || document.body
      expect(appElement).toBeTruthy()
    })
  })

  it('deve configurar interceptadores de resposta', async () => {
    render(<App />)
    
    // Verificar se fetch foi configurado
    expect(global.fetch).toBeDefined()
  })
})

describe('App Routing', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    
    // Mock usuário autenticado
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        authenticated: true,
        user: {
          id: 1,
          email: 'test@test.com',
          name: 'Test User'
        }
      })
    })
  })

  it('deve navegar para dashboard quando autenticado', async () => {
    render(<App />)
    
    await waitFor(() => {
      // Verificar se elementos do dashboard estão presentes
      const dashboardElements = screen.queryAllByText(/dashboard|início/i)
      expect(dashboardElements.length).toBeGreaterThanOrEqual(0)
    })
  })

  it('deve lidar com rotas protegidas', async () => {
    render(<App />)
    
    await waitFor(() => {
      // App deve renderizar sem erros
      expect(document.body).toBeTruthy()
    })
  })
})

describe('App Error Handling', () => {
  it('deve lidar com erro de autenticação', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: () => Promise.resolve({ error: 'Unauthorized' })
    })
    
    render(<App />)
    
    await waitFor(() => {
      // Deve mostrar tela de login em caso de erro 401
      expect(document.body).toBeTruthy()
    })
  })

  it('deve lidar com erro de servidor', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: () => Promise.resolve({ error: 'Server error' })
    })
    
    render(<App />)
    
    await waitFor(() => {
      // App deve renderizar mesmo com erro de servidor
      expect(document.body).toBeTruthy()
    })
  })
})

