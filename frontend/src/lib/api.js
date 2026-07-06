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
// Every ERP resource follows the same REST shape, so build fetch/create/
// update/remove functions from one factory instead of repeating axios calls.
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

export const assets = resource('assets')
export const assetCategories = resource('asset-categories')

export const leads = resource('leads')
export const opportunities = resource('opportunities')

export const printTemplates = resource('print-templates')

// ---- Backwards-compatible named fetchers (used by existing pages) -------
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
