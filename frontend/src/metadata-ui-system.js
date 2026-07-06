/**
 * Metadata-Driven UI System for Nexus SaaS ERP
 * Generates complete UI from backend metadata
 */

export class MetadataUISystem {
  constructor(metadata) {
    this.metadata = metadata;
    this.components = {};
  }

  /**
   * Generate complete page from metadata
   */
  generatePage(pageMetadata) {
    const { type, config } = pageMetadata;

    switch (type) {
      case 'list':
        return this.generateListPage(config);
      case 'detail':
        return this.generateDetailPage(config);
      case 'form':
        return this.generateFormPage(config);
      case 'dashboard':
        return this.generateDashboardPage(config);
      case 'report':
        return this.generateReportPage(config);
      case 'kanban':
        return this.generateKanbanPage(config);
      case 'calendar':
        return this.generateCalendarPage(config);
      case 'gantt':
        return this.generateGanttPage(config);
      case 'map':
        return this.generateMapPage(config);
      default:
        return this.generateGenericPage(config);
    }
  }

  /**
   * Generate List Page (Data Grid)
   */
  generateListPage(config) {
    return {
      layout: 'list',
      toolbar: {
        title: config.title,
        actions: [
          { type: 'create', label: 'New', icon: 'Add', route: `${config.route}/new` },
          { type: 'import', label: 'Import', icon: 'Upload' },
          { type: 'export', label: 'Export', icon: 'Download' },
        ],
        filters: config.filters?.map(f => ({
          field: f.name,
          type: f.type,
          label: f.label,
          options: f.options,
        })) || [],
      },
      dataGrid: {
        columns: config.fields.map(field => ({
          field: field.name,
          headerName: field.label,
          type: this.mapFieldTypeToGrid(field.type),
          width: field.width || 'auto',
          sortable: field.sortable !== false,
          filterable: field.filterable !== false,
          editable: field.editable || false,
          formatter: field.formatter,
          cellRenderer: field.cell_renderer,
        })),
        pagination: {
          pageSize: config.page_size || 25,
          pageSizeOptions: [10, 25, 50, 100],
        },
        sorting: {
          defaultSort: config.default_sort,
          multiSort: true,
        },
        grouping: config.group_by ? { field: config.group_by } : null,
        aggregation: config.aggregations || {},
        rowActions: [
          { type: 'view', icon: 'Visibility', route: `${config.route}/:id` },
          { type: 'edit', icon: 'Edit', route: `${config.route}/:id/edit` },
          { type: 'delete', icon: 'Delete', confirm: true },
          { type: 'duplicate', icon: 'ContentCopy' },
        ],
        bulkActions: [
          { type: 'delete', label: 'Delete Selected' },
          { type: 'export', label: 'Export Selected' },
          { type: 'assign', label: 'Assign To' },
        ],
      },
    };
  }

  /**
   * Generate Detail Page
   */
  generateDetailPage(config) {
    return {
      layout: 'detail',
      header: {
        title: config.title_field || 'name',
        subtitle: config.subtitle_field,
        status: config.status_field,
        avatar: config.avatar_field,
        breadcrumbs: config.breadcrumbs || [],
      },
      tabs: config.tabs?.map(tab => ({
        id: tab.id,
        label: tab.label,
        icon: tab.icon,
        content: this.generateTabContent(tab),
      })) || [
        { id: 'overview', label: 'Overview', content: this.generateOverviewTab(config) },
        { id: 'history', label: 'History', content: { type: 'timeline' } },
        { id: 'related', label: 'Related', content: { type: 'related_lists' } },
      ],
      sidebar: {
        sections: [
          { type: 'info_card', fields: config.summary_fields },
          { type: 'activity_feed', limit: 10 },
          { type: 'quick_actions', actions: config.quick_actions },
        ],
      },
    };
  }

  /**
   * Generate Form Page
   */
  generateFormPage(config) {
    return {
      layout: 'form',
      header: {
        title: config.is_edit ? `Edit ${config.entity_label}` : `New ${config.entity_label}`,
        breadcrumbs: config.breadcrumbs,
      },
      form: {
        schema: config.schema,
        sections: config.sections?.map(section => ({
          title: section.title,
          description: section.description,
          fields: section.fields,
          layout: section.layout || { type: 'grid', columns: 12 },
          collapsible: section.collapsible || false,
          defaultOpen: section.default_open !== false,
        })),
        validation: config.validation,
        submitAction: config.submit_action,
        cancelAction: config.cancel_action,
      },
    };
  }

  /**
   * Generate Dashboard Page
   */
  generateDashboardPage(config) {
    return {
      layout: 'dashboard',
      widgets: config.widgets?.map(widget => ({
        id: widget.id,
        type: widget.type, // 'kpi', 'chart', 'table', 'list', 'map'
        title: widget.title,
        size: widget.size || { w: 4, h: 3 },
        position: widget.position,
        config: widget.config,
        refreshInterval: widget.refresh_interval || 300,
      })) || [],
      layout: {
        type: 'grid',
        columns: 12,
        rowHeight: 80,
        draggable: true,
        resizable: true,
      },
    };
  }

  /**
   * Generate Report Page
   */
  generateReportPage(config) {
    return {
      layout: 'report',
      filters: config.filters,
      visualization: {
        type: config.chart_type || 'table',
        config: config.chart_config,
      },
      export: {
        formats: ['pdf', 'excel', 'csv', 'json'],
        scheduling: config.scheduling || false,
      },
    };
  }

  /**
   * Generate Kanban Board
   */
  generateKanbanPage(config) {
    return {
      layout: 'kanban',
      columns: config.status_values?.map(status => ({
        id: status.value,
        title: status.label,
        color: status.color,
        wip_limit: status.wip_limit,
      })) || [],
      card: {
        fields: config.card_fields,
        actions: config.card_actions,
      },
      dragDrop: {
        enabled: true,
        onDrop: config.on_status_change,
      },
    };
  }

  /**
   * Map field types to grid column types
   */
  mapFieldTypeToGrid(fieldType) {
    const typeMap = {
      string: 'string',
      text: 'string',
      number: 'number',
      integer: 'number',
      boolean: 'boolean',
      date: 'date',
      datetime: 'datetime',
      currency: 'currency',
      percentage: 'percentage',
      status: 'chip',
      avatar: 'avatar',
      image: 'image',
      email: 'email',
      url: 'link',
      reference: 'reference',
      rating: 'rating',
      color: 'color',
    };
    return typeMap[fieldType] || 'string';
  }

  /**
   * Generate navigation from metadata
   */
  generateNavigation(metadata) {
    return {
      sidebar: {
        items: metadata.modules?.map(module => ({
          id: module.id,
          label: module.label,
          icon: module.icon,
          route: module.route,
          children: module.entities?.map(entity => ({
            id: entity.id,
            label: entity.label,
            icon: entity.icon,
            route: `${module.route}/${entity.route}`,
            badge: entity.badge,
          })),
        })) || [],
      },
      quickAccess: metadata.quick_actions?.map(action => ({
        id: action.id,
        label: action.label,
        icon: action.icon,
        route: action.route,
        shortcut: action.shortcut,
      })) || [],
    };
  }
}

/**
 * Entity Metadata Manager
 * Fetches and caches entity metadata from backend
 */
export class EntityMetadataManager {
  constructor(apiClient) {
    this.api = apiClient;
    this.cache = new Map();
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
  }

  async getEntityMetadata(entityType) {
    if (this.cache.has(entityType)) {
      const cached = this.cache.get(entityType);
      if (Date.now() - cached.timestamp < this.cacheExpiry) {
        return cached.data;
      }
    }

    const response = await this.api.get(`/api/metadata/entities/${entityType}`);
    const metadata = response.data;

    this.cache.set(entityType, {
      data: metadata,
      timestamp: Date.now(),
    });

    return metadata;
  }

  async getPageMetadata(pageId) {
    const response = await this.api.get(`/api/metadata/pages/${pageId}`);
    return response.data;
  }

  async getDashboardMetadata(dashboardId) {
    const response = await this.api.get(`/api/metadata/dashboards/${dashboardId}`);
    return response.data;
  }

  invalidateCache(entityType) {
    this.cache.delete(entityType);
  }

  clearCache() {
    this.cache.clear();
  }
}

export default { MetadataUISystem, EntityMetadataManager };
