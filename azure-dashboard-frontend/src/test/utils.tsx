import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ReactElement, ReactNode } from 'react'

// Mock do contexto de autenticação
const MockAuthProvider = ({ children }: { children: ReactNode }) => {
  return <div data-testid="auth-provider">{children}</div>
}

// Wrapper customizado para testes
const AllTheProviders = ({ children }: { children: ReactNode }) => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        {children}
      </MockAuthProvider>
    </BrowserRouter>
  )
}

// Função de render customizada
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options })

// Mock de dados para testes
export const mockUser = {
  id: 1,
  email: 'test@test.com',
  name: 'Test User',
  is_admin: false,
  created_at: '2024-01-01T00:00:00Z'
}

export const mockAzureCredentials = {
  tenant_id: 'test-tenant-id',
  client_id: 'test-client-id',
  subscription_id: 'test-subscription-id',
  subscription_name: 'Test Subscription'
}

export const mockResourceGroup = {
  id: '/subscriptions/test/resourceGroups/test-rg',
  name: 'test-rg',
  location: 'eastus',
  properties: {
    provisioningState: 'Succeeded'
  }
}

export const mockCostData = {
  total_cost: 150.75,
  currency: 'USD',
  billing_period: '2024-01',
  daily_costs: [
    { date: '2024-01-01', cost: 5.25 },
    { date: '2024-01-02', cost: 4.80 }
  ]
}

// Função para criar mock de fetch response
export const createMockResponse = (data: any, status = 200) => {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  } as Response)
}

// Mock de APIs
export const mockApiResponses = {
  login: createMockResponse({ 
    message: 'Login successful', 
    user: mockUser 
  }),
  
  azureResources: createMockResponse([mockResourceGroup]),
  
  azureCosts: createMockResponse(mockCostData),
  
  health: createMockResponse({ status: 'healthy' }),
  
  authStatus: createMockResponse({ 
    authenticated: true, 
    user: mockUser 
  })
}

// Função para aguardar loading states
export const waitForLoadingToFinish = () => {
  return new Promise(resolve => setTimeout(resolve, 0))
}

// Re-export tudo do testing-library
export * from '@testing-library/react'
export { customRender as render }

