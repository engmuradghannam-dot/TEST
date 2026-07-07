import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Token ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

// ---- Generic CRUD helper -------------------------------------------------
function resource(path) {
  return {
    list: (params) => api.get(`/${path}/`, { params }).then((r) => r.data),
    get: (id) => api.get(`/${path}/${id}/`).then((r) => r.data),
    create: (data) => api.post(`/${path}/`, data).then((r) => r.data),
    update: (id, data) => api.patch(`/${path}/${id}/`, data).then((r) => r.data),
    remove: (id) => api.delete(`/${path}/${id}/`),
  }
}

export const companies = resource('companies')
export const branches = resource('branches')
export const warehouses = resource('warehouses')
export const users = resource('users')

export const purchaseOrders = resource('purchase-orders')
export const purchaseOrderItems = resource('purchase-order-items')
export const purchaseTaxCharges = resource('purchase-tax-charges')
export const purchasePayments = resource('purchase-payments')
export const suppliers = resource('suppliers')

export const salesOrders = resource('sales-orders')
export const salesOrderItems = resource('sales-order-items')
export const salesTaxCharges = resource('sales-tax-charges')
export const salesPayments = resource('sales-payments')
export const customers = resource('customers')

export const items = resource('items')
export const itemGroups = resource('item-groups')
export const stockEntries = resource('stock-entries')
export const stockReconciliations = resource('stock-reconciliations')
export const stockReconciliationItems = resource('stock-reconciliation-items')

export const employees = resource('employees')
export const departments = resource('departments')
export const teams = resource('teams')
export const leaveRequests = resource('leave-requests')
export const payrolls = resource('payrolls')

export const accounts = resource('accounts')
export const journalEntries = resource('journal-entries')
export const costCenters = resource('cost-centers')
export const budgets = resource('budgets')

export const workOrders = resource('work-orders')
export const boms = resource('boms')
export const bomItems = resource('bom-items')

export const projects = resource('projects')
export const tasks = resource('tasks')
export const milestones = resource('milestones')
export const stakeholders = resource('stakeholders')
export const risks = resource('risks')
export const issues = resource('issues')
export const changeRequests = resource('change-requests')
export const timeEntries = resource('time-entries')
export const taskComments = resource('task-comments')

export const assets = resource('assets')
export const assetCategories = resource('asset-categories')

export const leads = resource('leads')
export const opportunities = resource('opportunities')

export const printTemplates = resource('print-templates')

// ---- Custom API calls for PM features ----
export const projectApi = {
  timeline: (id) => api.get(`/projects/${id}/timeline/`).then((r) => r.data),
  kanban: (id) => api.get(`/projects/${id}/kanban/`).then((r) => r.data),
  timeReport: (id) => api.get(`/projects/${id}/time_report/`).then((r) => r.data),
}

export const taskApi = {
  startTimer: (id, data) => api.post(`/tasks/${id}/start_timer/`, data).then((r) => r.data),
  stopTimer: (id, data) => api.post(`/tasks/${id}/stop_timer/`, data).then((r) => r.data),
  comments: (id) => api.get(`/tasks/${id}/comments/`).then((r) => r.data),
}

export const timeEntryApi = {
  myEntries: () => api.get('/time-entries/my_entries/').then((r) => r.data),
  dashboard: () => api.get('/time-entries/dashboard/').then((r) => r.data),
}

// ---- Backwards-compatible named fetchers ----
export const fetchPurchaseOrders = purchaseOrders.list
export const fetchSalesOrders = salesOrders.list
export const fetchEmployees = employees.list
export const fetchCompanies = companies.list
export const fetchSuppliers = suppliers.list
export const fetchCustomers = customers.list
export const fetchWorkOrders = workOrders.list
export const fetchItems = items.list
export const fetchAccounts = accounts.list
export const fetchProjects = projects.list
export const fetchAssets = assets.list
export const fetchLeads = leads.list

export default api

// ── KPI & Analytics ───────────────────────────────────────────────────────
export const kpiDefinitions    = resource('kpi/definitions')
export const companyKpis       = resource('kpi/company-kpis')
export const kpiHistory        = resource('kpi/history')
export const dashboardWidgets  = resource('kpi/dashboard-widgets')

// ── Market & Localization ─────────────────────────────────────────────────
export const countryLocalizations = resource('market/localizations')
export const certifications    = resource('market/certifications')
export const partners          = resource('market/partners')
export const marketplaceApps   = resource('market/apps')

// ── Industries ────────────────────────────────────────────────────────────
export const industryCatalog   = resource('industries/industry-catalogs')
export const industryControls  = resource('industries/industry-controls')
export const aiAgentRegistry   = resource('industries/ai-agent-registrys')

// ── Events ────────────────────────────────────────────────────────────────
export const eventStore        = resource('events/event-stores')
export const eventHandlers     = resource('events/event-handlers')

// ── IAM & Security ────────────────────────────────────────────────────────
export const identityProviders  = resource('iam/providers')
export const privilegedSessions = resource('iam/privileged-sessions')
export const roleMiningJobs     = resource('iam/role-mining-jobs')
export const securityEvents     = resource('iam/security-events')

// ── Compliance ────────────────────────────────────────────────────────────
export const complianceFrameworks = resource('compliance/frameworks')
export const complianceAssessments = resource('compliance/assessments')

// ── Manufacturing ─────────────────────────────────────────────────────────
// DEDUP: export const bomItems          = resource('manufacturing/bom-items')

// ── Reports ───────────────────────────────────────────────────────────────
export const reports = {
  trialBalance:     (params) => api.get('/accounts/reports/trial-balance/', { params }).then(r => r.data),
  incomeStatement:  (params) => api.get('/accounts/reports/income-statement/', { params }).then(r => r.data),
  balanceSheet:     (params) => api.get('/accounts/reports/balance-sheet/', { params }).then(r => r.data),
  kpis:             ()       => api.get('/accounts/reports/kpis/').then(r => r.data),
}

// ── AI & NLP ──────────────────────────────────────────────────────────────
export const nlErp = {
  query:    (text)      => api.post('/ai/nl/', { text }).then(r => r.data),
  forecast: ()          => api.get('/ai/forecast/sales/').then(r => r.data),
  health:   ()          => api.get('/ai/core/health/').then(r => r.data),
}

// ── Onboarding & ZATCA ────────────────────────────────────────────────────
export const onboarding = {
  register: (data)      => api.post('/tenants/onboarding/register/', data).then(r => r.data),
  setup:    (options)   => api.post('/tenants/onboarding/setup/', { options }).then(r => r.data),
  importCsv:(entity, csv) => api.post('/tenants/onboarding/import-data/', { entity, csv }).then(r => r.data),
  status:   ()          => api.get('/tenants/onboarding/status/').then(r => r.data),
  zatca:    (data)      => api.post('/tenants/onboarding/zatca/', data).then(r => r.data),
}

// ── Health ────────────────────────────────────────────────────────────────
export const system = {
  health: () => api.get('/core/health/').then(r => r.data),
  ready:  () => api.get('/core/ready/').then(r => r.data),
}
// ── Password Reset ────────────────────────────────────────────────────────
export const passwordReset = {
  request: (email)              => api.post('/accounts/password/reset/', { email }).then(r => r.data),
  confirm: (token, new_password) => api.post('/accounts/password/confirm/', { token, new_password }).then(r => r.data),
}
