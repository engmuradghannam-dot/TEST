import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  Plus, Trash2, ArrowUp, ArrowDown, Save, Eye, PencilRuler, List,
} from 'lucide-react';
import api from '../lib/api';
import FormEngine from '../components/FormEngine';

/**
 * ScreenBuilder — low-code screens builder.
 * Compose a data-entry screen from a field palette, preview it live
 * (rendered by the same FormEngine end users get), and save it as a
 * UIScreen the API serves at /core/ui-screens/.
 */

const FIELD_TYPES = [
  'text', 'number', 'decimal', 'date', 'select',
  'checkbox', 'textarea', 'email', 'phone',
];

const EMPTY_FIELD = () => ({
  name: '', type: 'text', label: '', label_ar: '',
  required: false, section: '', options: [],
});

function FieldEditor({ field, index, count, onChange, onMove, onRemove }) {
  const set = (k, v) => onChange(index, { ...field, [k]: v });
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-mono text-gray-400">#{index + 1}</span>
        <div className="flex gap-1">
          <button onClick={() => onMove(index, -1)} disabled={index === 0}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30">
            <ArrowUp size={14} />
          </button>
          <button onClick={() => onMove(index, 1)} disabled={index === count - 1}
            className="rounded p-1 text-gray-400 hover:bg-gray-100 disabled:opacity-30">
            <ArrowDown size={14} />
          </button>
          <button onClick={() => onRemove(index)}
            className="rounded p-1 text-red-400 hover:bg-red-50">
            <Trash2 size={14} />
          </button>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2">
        <input value={field.name} onChange={(e) => set('name', e.target.value)}
          placeholder="field_name" className="rounded border border-gray-300 px-2 py-1 text-sm font-mono" />
        <select value={field.type} onChange={(e) => set('type', e.target.value)}
          className="rounded border border-gray-300 px-2 py-1 text-sm">
          {FIELD_TYPES.map((t) => <option key={t}>{t}</option>)}
        </select>
        <input value={field.label} onChange={(e) => set('label', e.target.value)}
          placeholder="Label (EN)" className="rounded border border-gray-300 px-2 py-1 text-sm" />
        <input value={field.label_ar} onChange={(e) => set('label_ar', e.target.value)}
          placeholder="التسمية (عربي)" dir="rtl" className="rounded border border-gray-300 px-2 py-1 text-sm" />
        <input value={field.section} onChange={(e) => set('section', e.target.value)}
          placeholder="Section (optional)" className="rounded border border-gray-300 px-2 py-1 text-sm" />
        <label className="flex items-center gap-2 text-sm text-gray-600">
          <input type="checkbox" checked={field.required}
            onChange={(e) => set('required', e.target.checked)}
            className="h-4 w-4 rounded border-gray-300 text-indigo-600" />
          Required
        </label>
      </div>
      {field.type === 'select' && (
        <input
          value={(field.options || []).map((o) => o.value).join(',')}
          onChange={(e) => set('options',
            e.target.value.split(',').filter(Boolean)
              .map((v) => ({ value: v.trim(), label: v.trim() })))}
          placeholder="Options, comma separated"
          className="w-full rounded border border-gray-300 px-2 py-1 text-sm" />
      )}
    </div>
  );
}

export default function ScreenBuilder() {
  const [screens, setScreens] = useState([]);
  const [slug, setSlug] = useState('');
  const [title, setTitle] = useState('');
  const [titleAr, setTitleAr] = useState('');
  const [endpoint, setEndpoint] = useState('');
  const [layout, setLayout] = useState('two-col');
  const [fields, setFields] = useState([EMPTY_FIELD()]);
  const [previewLang, setPreviewLang] = useState('en');
  const [saving, setSaving] = useState(false);

  const loadScreens = () =>
    api.get('/core/ui-screens/').then((r) => setScreens(r.data.results || r.data)).catch(() => {});
  useEffect(() => { loadScreens(); }, []);

  const changeField = (i, f) => setFields(fields.map((x, j) => (j === i ? f : x)));
  const moveField = (i, d) => {
    const next = [...fields];
    [next[i], next[i + d]] = [next[i + d], next[i]];
    setFields(next);
  };
  const removeField = (i) => setFields(fields.filter((_, j) => j !== i));

  const schema = { layout, fields: fields.filter((f) => f.name) };

  const save = async () => {
    if (!slug || !title) { toast.error('Slug and title are required'); return; }
    if (!schema.fields.length) { toast.error('Add at least one named field'); return; }
    setSaving(true);
    try {
      await api.post('/core/ui-screens/', {
        slug, title, title_ar: titleAr, schema, target_endpoint: endpoint,
      });
      toast.success(`Screen "${title}" saved`);
      loadScreens();
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Save failed');
    } finally {
      setSaving(false);
    }
  };

  const loadExisting = (s) => {
    setSlug(s.slug); setTitle(s.title); setTitleAr(s.title_ar || '');
    setEndpoint(s.target_endpoint || '');
    setLayout(s.schema?.layout || 'two-col');
    setFields(s.schema?.fields?.length ? s.schema.fields : [EMPTY_FIELD()]);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center gap-3">
        <PencilRuler className="text-indigo-600" />
        <div>
          <h1 className="text-xl font-bold text-gray-800">Screen Builder</h1>
          <p className="text-sm text-gray-500">
            Build data-entry screens without code — saved screens render through FormEngine.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* ── Builder ─────────────────────────────── */}
        <div className="space-y-4">
          <div className="rounded-xl border bg-white p-4 shadow-sm space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <input value={slug} onChange={(e) => setSlug(e.target.value)}
                placeholder="screen-slug" className="rounded border border-gray-300 px-3 py-2 text-sm font-mono" />
              <select value={layout} onChange={(e) => setLayout(e.target.value)}
                className="rounded border border-gray-300 px-3 py-2 text-sm">
                <option value="single">Single column</option>
                <option value="two-col">Two columns</option>
              </select>
              <input value={title} onChange={(e) => setTitle(e.target.value)}
                placeholder="Screen title (EN)" className="rounded border border-gray-300 px-3 py-2 text-sm" />
              <input value={titleAr} onChange={(e) => setTitleAr(e.target.value)}
                placeholder="عنوان الشاشة" dir="rtl" className="rounded border border-gray-300 px-3 py-2 text-sm" />
            </div>
            <input value={endpoint} onChange={(e) => setEndpoint(e.target.value)}
              placeholder="Target endpoint e.g. /crm/leads/"
              className="w-full rounded border border-gray-300 px-3 py-2 text-sm font-mono" />
          </div>

          <div className="space-y-3">
            {fields.map((f, i) => (
              <FieldEditor key={i} field={f} index={i} count={fields.length}
                onChange={changeField} onMove={moveField} onRemove={removeField} />
            ))}
          </div>

          <div className="flex gap-2">
            <button onClick={() => setFields([...fields, EMPTY_FIELD()])}
              className="flex items-center gap-1 rounded-lg border border-gray-300 bg-white px-4 py-2 text-sm hover:bg-gray-50">
              <Plus size={16} /> Add field
            </button>
            <button onClick={save} disabled={saving}
              className="flex items-center gap-1 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
              <Save size={16} /> {saving ? 'Saving…' : 'Save screen'}
            </button>
          </div>

          {screens.length > 0 && (
            <div className="rounded-xl border bg-white p-4 shadow-sm">
              <h3 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-600">
                <List size={16} /> Saved screens
              </h3>
              <ul className="divide-y divide-gray-100">
                {screens.map((s) => (
                  <li key={s.slug} className="flex items-center justify-between py-2">
                    <span className="text-sm text-gray-700">{s.title}
                      <span className="mx-2 font-mono text-xs text-gray-400">{s.slug}</span>
                    </span>
                    <button onClick={() => loadExisting(s)}
                      className="text-sm text-indigo-600 hover:underline">Edit</button>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>

        {/* ── Live preview ────────────────────────── */}
        <div className="rounded-xl border bg-white p-4 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <h3 className="flex items-center gap-2 text-sm font-semibold text-gray-600">
              <Eye size={16} /> Live preview
            </h3>
            <div className="flex overflow-hidden rounded-lg border border-gray-200 text-xs">
              {['en', 'ar'].map((l) => (
                <button key={l} onClick={() => setPreviewLang(l)}
                  className={`px-3 py-1 ${previewLang === l
                    ? 'bg-indigo-600 text-white' : 'bg-white text-gray-600'}`}>
                  {l === 'en' ? 'English' : 'عربي'}
                </button>
              ))}
            </div>
          </div>
          {schema.fields.length === 0 ? (
            <p className="py-12 text-center text-sm text-gray-400">
              Name your first field to see the preview.
            </p>
          ) : (
            <FormEngine schema={schema} lang={previewLang}
              submitLabel={previewLang === 'ar' ? 'إرسال' : 'Submit'}
              onSubmit={(v) => toast.success('Preview submit: ' + JSON.stringify(v))} />
          )}
        </div>
      </div>
    </div>
  );
}
