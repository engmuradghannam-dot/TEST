/**
 * Dynamic Form Engine for Nexus SaaS ERP
 * Generates forms from JSON schema/metadata
 */

export class DynamicFormEngine {
  constructor(schema, options = {}) {
    this.schema = schema;
    this.options = {
      validateOnChange: true,
      validateOnBlur: true,
      ...options
    };
    this.fields = {};
    this.errors = {};
    this.values = {};
  }

  /**
   * Generate form fields from schema
   */
  generateFields() {
    return this.schema.fields.map(field => ({
      ...field,
      component: this.getComponentType(field.type),
      props: this.getFieldProps(field),
      validators: this.buildValidators(field),
    }));
  }

  /**
   * Map schema types to UI components
   */
  getComponentType(type) {
    const componentMap = {
      string: 'TextField',
      text: 'TextArea',
      number: 'NumberField',
      integer: 'NumberField',
      boolean: 'Switch',
      date: 'DatePicker',
      datetime: 'DateTimePicker',
      time: 'TimePicker',
      email: 'EmailField',
      password: 'PasswordField',
      url: 'URLField',
      tel: 'PhoneField',
      select: 'Select',
      multiselect: 'MultiSelect',
      autocomplete: 'Autocomplete',
      radio: 'RadioGroup',
      checkbox: 'CheckboxGroup',
      file: 'FileUpload',
      image: 'ImageUpload',
      rich_text: 'RichTextEditor',
      code: 'CodeEditor',
      json: 'JSONEditor',
      currency: 'CurrencyField',
      percentage: 'PercentageField',
      rating: 'Rating',
      color: 'ColorPicker',
      signature: 'SignaturePad',
      barcode: 'BarcodeScanner',
      qr_code: 'QRCodeGenerator',
      reference: 'ReferenceField',
      lookup: 'LookupField',
      formula: 'FormulaField',
      grid: 'DataGrid',
      table: 'TableField',
      tabs: 'TabsField',
      section: 'SectionField',
      divider: 'DividerField',
    };
    return componentMap[type] || 'TextField';
  }

  /**
   * Build field props from schema
   */
  getFieldProps(field) {
    return {
      name: field.name,
      label: field.label || field.name,
      placeholder: field.placeholder,
      helperText: field.description,
      required: field.required || false,
      disabled: field.readonly || false,
      hidden: field.hidden || false,
      defaultValue: field.default,

      // Layout
      gridColumn: field.grid_column || 'span 12',
      gridRow: field.grid_row,

      // Styling
      size: field.size || 'medium',
      variant: field.variant || 'outlined',
      fullWidth: field.fullWidth !== false,

      // Options for select/autocomplete
      options: field.options || [],
      optionLabel: field.option_label || 'label',
      optionValue: field.option_value || 'value',

      // Async loading
      loadOptions: field.load_options,
      searchDelay: field.search_delay || 300,

      // Validation
      min: field.min,
      max: field.max,
      minLength: field.min_length,
      maxLength: field.max_length,
      pattern: field.pattern,

      // Conditional rendering
      visibleWhen: field.visible_when,
      enabledWhen: field.enabled_when,

      // ERP-specific
      entityType: field.entity_type,
      entityField: field.entity_field,
      filters: field.filters,

      // Custom props
      ...field.custom_props,
    };
  }

  /**
   * Build validators from schema rules
   */
  buildValidators(field) {
    const validators = [];

    if (field.required) {
      validators.push({
        type: 'required',
        message: field.required_message || `${field.label} is required`,
      });
    }

    if (field.min_length) {
      validators.push({
        type: 'minLength',
        value: field.min_length,
        message: `Minimum ${field.min_length} characters`,
      });
    }

    if (field.max_length) {
      validators.push({
        type: 'maxLength',
        value: field.max_length,
        message: `Maximum ${field.max_length} characters`,
      });
    }

    if (field.min !== undefined) {
      validators.push({
        type: 'min',
        value: field.min,
        message: `Minimum value is ${field.min}`,
      });
    }

    if (field.max !== undefined) {
      validators.push({
        type: 'max',
        value: field.max,
        message: `Maximum value is ${field.max}`,
      });
    }

    if (field.pattern) {
      validators.push({
        type: 'pattern',
        value: new RegExp(field.pattern),
        message: field.pattern_message || 'Invalid format',
      });
    }

    if (field.email) {
      validators.push({
        type: 'email',
        message: 'Invalid email address',
      });
    }

    if (field.unique) {
      validators.push({
        type: 'unique',
        entity: field.entity_type,
        field: field.name,
        message: `${field.label} must be unique`,
      });
    }

    // Custom validators
    if (field.validators) {
      validators.push(...field.validators);
    }

    return validators;
  }

  /**
   * Validate a single field
   */
  validateField(name, value) {
    const field = this.schema.fields.find(f => f.name === name);
    if (!field) return null;

    const validators = this.buildValidators(field);

    for (const validator of validators) {
      const error = this.runValidator(validator, value);
      if (error) return error;
    }

    return null;
  }

  /**
   * Run a single validator
   */
  runValidator(validator, value) {
    switch (validator.type) {
      case 'required':
        return value === undefined || value === null || value === '' ? validator.message : null;
      case 'minLength':
        return value && value.length < validator.value ? validator.message : null;
      case 'maxLength':
        return value && value.length > validator.value ? validator.message : null;
      case 'min':
        return value < validator.value ? validator.message : null;
      case 'max':
        return value > validator.value ? validator.message : null;
      case 'pattern':
        return !validator.value.test(value) ? validator.message : null;
      case 'email':
        return !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? validator.message : null;
      default:
        return null;
    }
  }

  /**
   * Validate entire form
   */
  validate(values) {
    const errors = {};

    for (const field of this.schema.fields) {
      const error = this.validateField(field.name, values[field.name]);
      if (error) {
        errors[field.name] = error;
      }
    }

    return errors;
  }

  /**
   * Apply conditional logic
   */
  applyConditions(values) {
    const visibleFields = new Set();
    const enabledFields = new Set();

    for (const field of this.schema.fields) {
      // Check visibility
      if (field.visible_when) {
        const isVisible = this.evaluateCondition(field.visible_when, values);
        if (isVisible) visibleFields.add(field.name);
      } else {
        visibleFields.add(field.name);
      }

      // Check enabled state
      if (field.enabled_when) {
        const isEnabled = this.evaluateCondition(field.enabled_when, values);
        if (isEnabled) enabledFields.add(field.name);
      } else {
        enabledFields.add(field.name);
      }
    }

    return { visibleFields, enabledFields };
  }

  /**
   * Evaluate conditional expression
   */
  evaluateCondition(condition, values) {
    const { field, operator, value } = condition;
    const fieldValue = values[field];

    switch (operator) {
      case 'equals': return fieldValue === value;
      case 'not_equals': return fieldValue !== value;
      case 'contains': return fieldValue?.includes(value);
      case 'not_contains': return !fieldValue?.includes(value);
      case 'gt': return fieldValue > value;
      case 'gte': return fieldValue >= value;
      case 'lt': return fieldValue < value;
      case 'lte': return fieldValue <= value;
      case 'empty': return !fieldValue;
      case 'not_empty': return !!fieldValue;
      case 'in': return value.includes(fieldValue);
      case 'not_in': return !value.includes(fieldValue);
      default: return true;
    }
  }
}

/**
 * Form Schema Builder - Build schemas from metadata
 */
export class FormSchemaBuilder {
  static fromEntity(entityConfig) {
    return {
      title: entityConfig.label,
      description: entityConfig.description,
      fields: entityConfig.fields.map(field => ({
        name: field.name,
        type: field.type,
        label: field.label,
        required: field.required,
        ...field,
      })),
      layout: entityConfig.layout || {
        type: 'grid',
        columns: 12,
        gap: 16,
      },
      actions: entityConfig.actions || [
        { type: 'submit', label: 'Save', variant: 'primary' },
        { type: 'reset', label: 'Reset', variant: 'secondary' },
        { type: 'cancel', label: 'Cancel', variant: 'text' },
      ],
    };
  }

  static fromWorkflow(workflowConfig) {
    return {
      title: workflowConfig.name,
      fields: workflowConfig.form_fields || [],
      layout: {
        type: 'wizard',
        steps: workflowConfig.steps || [],
      },
    };
  }
}

export default DynamicFormEngine;
