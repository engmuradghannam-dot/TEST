import React, { useState } from 'react';
import { AlertCircle } from 'lucide-react';

/**
 * FormEngine — renders a working form from a UIScreen JSON schema.
 *
 * schema = {
 *   layout: 'single' | 'two-col',
 *   fields: [{
 *     name, type: 'text|number|decimal|date|select|checkbox|textarea|email|phone',
 *     label, label_ar, required, options: [{value,label,label_ar}],
 *     default, min, max, placeholder, section
 *   }]
 * }
 *
 * Bilingual: pass lang="ar" for Arabic labels + RTL.
 */

const INPUT_BASE =
  'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm ' +
  'focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 ' +
  'disabled:bg-gray-50';

function validateField(field, value) {
  const label = field.label || field.name;
  if (field.required && (value === undefined || value === null || value === ''))
    return `${label} is required`;
  if (value === '' || value === undefined || value === null) return null;
  if (['number', 'decimal'].includes(field.type)) {
    const n = Number(value);
    if (Number.isNaN(n)) return `${label} must be a number`;
    if (field.min !== undefined && n < field.min) return `${label} ≥ ${field.min}`;
    if (field.max !== undefined && n > field.max) return `${label} ≤ ${field.max}`;
  }
  if (field.type === 'email' && !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value))
    return `${label}: invalid email`;
  return null;
}

function Field({ field, value, error, onChange, lang }) {
  const label = lang === 'ar' && field.label_ar ? field.label_ar : field.label || field.name;
  const common = {
    id: field.name,
    value: value ?? '',
    placeholder: field.placeholder || '',
    onChange: (e) => onChange(field.name, e.target.type === 'checkbox' ? e.target.checked : e.target.value),
    className: INPUT_BASE + (error ? ' border-red-400' : ''),
  };

  let control;
  switch (field.type) {
    case 'textarea':
      control = <textarea rows={3} {...common} />;
      break;
    case 'select':
      control = (
        <select {...common}>
          <option value="">—</option>
          {(field.options || []).map((o) => (
            <option key={o.value} value={o.value}>
              {lang === 'ar' && o.label_ar ? o.label_ar : o.label}
            </option>
          ))}
        </select>
      );
      break;
    case 'checkbox':
      control = (
        <input type="checkbox" id={field.name} checked={!!value}
          onChange={common.onChange}
          className="h-4 w-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" />
      );
      break;
    case 'number':
    case 'decimal':
      control = <input type="number" step={field.type === 'decimal' ? '0.01' : '1'} {...common} />;
      break;
    case 'date':
      control = <input type="date" {...common} />;
      break;
    default:
      control = <input type={field.type === 'email' ? 'email' : 'text'} {...common} />;
  }

  return (
    <div className={field.type === 'checkbox' ? 'flex items-center gap-2' : ''}>
      <label htmlFor={field.name}
        className="block text-sm font-medium text-gray-700 mb-1">
        {label}{field.required && <span className="text-red-500 mx-0.5">*</span>}
      </label>
      {control}
      {error && (
        <p className="mt-1 flex items-center gap-1 text-xs text-red-600">
          <AlertCircle size={12} /> {error}
        </p>
      )}
    </div>
  );
}

export default function FormEngine({ schema, lang = 'en', initialValues = {},
  onSubmit, submitLabel, busy = false }) {
  const fields = schema?.fields || [];
  const [values, setValues] = useState(() => {
    const v = { ...initialValues };
    fields.forEach((f) => {
      if (v[f.name] === undefined && f.default !== undefined) v[f.name] = f.default;
    });
    return v;
  });
  const [errors, setErrors] = useState({});

  const handleChange = (name, value) => {
    setValues((prev) => ({ ...prev, [name]: value }));
    setErrors((prev) => ({ ...prev, [name]: null }));
  };

  const handleSubmit = () => {
    const errs = {};
    fields.forEach((f) => {
      const e = validateField(f, values[f.name]);
      if (e) errs[f.name] = e;
    });
    setErrors(errs);
    if (Object.keys(errs).length === 0 && onSubmit) onSubmit(values);
  };

  // group by section
  const sections = [];
  fields.forEach((f) => {
    const name = f.section || '';
    let sec = sections.find((s) => s.name === name);
    if (!sec) { sec = { name, fields: [] }; sections.push(sec); }
    sec.fields.push(f);
  });

  const grid = schema?.layout === 'two-col'
    ? 'grid grid-cols-1 md:grid-cols-2 gap-4'
    : 'space-y-4';

  return (
    <div dir={lang === 'ar' ? 'rtl' : 'ltr'} className="space-y-6">
      {sections.map((sec) => (
        <div key={sec.name}>
          {sec.name && (
            <h4 className="mb-3 border-b border-gray-200 pb-1 text-sm font-semibold text-gray-600">
              {sec.name}
            </h4>
          )}
          <div className={grid}>
            {sec.fields.map((f) => (
              <Field key={f.name} field={f} value={values[f.name]}
                error={errors[f.name]} onChange={handleChange} lang={lang} />
            ))}
          </div>
        </div>
      ))}
      <button type="button" onClick={handleSubmit} disabled={busy}
        className="rounded-lg bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
        {busy ? '…' : submitLabel || (lang === 'ar' ? 'حفظ' : 'Save')}
      </button>
    </div>
  );
}
