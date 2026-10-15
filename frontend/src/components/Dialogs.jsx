import { useEffect, useState } from 'react';
import Icon from './Icon.jsx';

const EMPTY = {
  sku: '',
  name: '',
  category: '',
  quantity: 0,
  reorder_level: 10,
  unit_price: '0.00',
  location: '',
  supplier: '',
  notes: '',
};

function useEscape(onClose) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
}

export function ProductDrawer({ product, categories, onClose, onSave }) {
  const editing = Boolean(product?.id);
  const [form, setForm] = useState(() => (editing ? { ...EMPTY, ...product, unit_price: String(product.unit_price) } : EMPTY));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  useEscape(onClose);

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    const payload = {
      name: form.name,
      category: form.category,
      quantity: Number(form.quantity),
      reorder_level: Number(form.reorder_level),
      unit_price: form.unit_price || '0',
      location: form.location,
      supplier: form.supplier,
      notes: form.notes,
    };
    if (!editing) payload.sku = form.sku;
    try {
      await onSave(payload, product?.id);
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <aside className="drawer" role="dialog" aria-modal="true" aria-labelledby="drawer-title">
        <form onSubmit={submit} className="drawer__form">
          <header className="drawer__head">
            <div>
              <p className="eyebrow eyebrow--dark">{editing ? product.sku : 'New SKU'}</p>
              <h2 id="drawer-title">{editing ? 'Edit product' : 'Add a product'}</h2>
            </div>
            <button type="button" className="icon-btn" onClick={onClose} aria-label="Close">
              <Icon name="close" />
            </button>
          </header>

          <div className="drawer__body">
            <div className="field-row">
              <label className="field">
                <span>SKU</span>
                <input value={form.sku} onChange={set('sku')} required disabled={editing} placeholder="PKG-1010" pattern="[A-Za-z0-9-]{3,32}" />
              </label>
              <label className="field">
                <span>Bin / location</span>
                <input value={form.location} onChange={set('location')} placeholder="A-04" />
              </label>
            </div>
            <label className="field">
              <span>Product name</span>
              <input value={form.name} onChange={set('name')} required minLength={2} placeholder="Corrugated box 40x30x20" />
            </label>
            <div className="field-row">
              <label className="field">
                <span>Category</span>
                <input value={form.category} onChange={set('category')} required minLength={2} list="category-options" placeholder="Packaging" />
                <datalist id="category-options">
                  {categories.map((c) => <option key={c} value={c} />)}
                </datalist>
              </label>
              <label className="field">
                <span>Supplier</span>
                <input value={form.supplier} onChange={set('supplier')} placeholder="Northline Packaging" />
              </label>
            </div>
            <div className="field-row field-row--3">
              <label className="field">
                <span>{editing ? 'On hand (count)' : 'Opening stock'}</span>
                <input type="number" min="0" value={form.quantity} onChange={set('quantity')} />
              </label>
              <label className="field">
                <span>Reorder at</span>
                <input type="number" min="0" value={form.reorder_level} onChange={set('reorder_level')} />
              </label>
              <label className="field">
                <span>Unit price (₹)</span>
                <input type="number" min="0" step="0.01" value={form.unit_price} onChange={set('unit_price')} />
              </label>
            </div>
            {editing && <p className="hint">Changing “On hand” records a stock-count entry in the movement ledger.</p>}
            <label className="field">
              <span>Notes</span>
              <textarea rows={3} value={form.notes} onChange={set('notes')} placeholder="Pack size, handling, lead time…" />
            </label>
            {error && <p className="form-error" role="alert">{error}</p>}
          </div>

          <footer className="drawer__foot">
            <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
            <button type="submit" className="btn btn--primary" disabled={saving}>
              {saving ? 'Saving…' : editing ? 'Save changes' : 'Add product'}
            </button>
          </footer>
        </form>
      </aside>
    </div>
  );
}

const REASONS = [
  { value: 'RECEIVED', label: 'Received', sign: 1 },
  { value: 'RETURNED', label: 'Returned', sign: 1 },
  { value: 'SOLD', label: 'Picked / sold', sign: -1 },
  { value: 'DAMAGED', label: 'Write-off', sign: -1 },
];

export function AdjustDialog({ product, initial, onClose, onSubmit }) {
  const [reason, setReason] = useState(initial?.reason ?? 'RECEIVED');
  const [amount, setAmount] = useState(initial?.amount ?? 1);
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  useEscape(onClose);

  const sign = REASONS.find((r) => r.value === reason).sign;
  const after = product.quantity + sign * Number(amount || 0);

  async function submit(e) {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSubmit(product.id, { delta: sign * Number(amount), reason, note });
    } catch (err) {
      setError(err.message);
      setSaving(false);
    }
  }

  return (
    <div className="overlay overlay--center" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form className="dialog" role="dialog" aria-modal="true" aria-labelledby="adjust-title" onSubmit={submit}>
        <header className="dialog__head">
          <div>
            <p className="eyebrow eyebrow--dark"><code>{product.sku}</code></p>
            <h2 id="adjust-title">{product.name}</h2>
          </div>
          <button type="button" className="icon-btn" onClick={onClose} aria-label="Close"><Icon name="close" /></button>
        </header>

        <div className="reason-grid" role="radiogroup" aria-label="Reason">
          {REASONS.map((r) => (
            <button
              key={r.value}
              type="button"
              role="radio"
              aria-checked={reason === r.value}
              className={`reason ${reason === r.value ? 'is-active' : ''}`}
              onClick={() => setReason(r.value)}
            >
              <Icon name={r.sign > 0 ? 'inbound' : 'outbound'} size={16} />
              {r.label}
            </button>
          ))}
        </div>

        <div className="stepper">
          <button type="button" className="icon-btn icon-btn--boxed" onClick={() => setAmount((a) => Math.max(1, Number(a) - 1))} aria-label="Decrease">
            <Icon name="minus" />
          </button>
          <input type="number" min="1" value={amount} onChange={(e) => setAmount(e.target.value)} aria-label="Units" />
          <button type="button" className="icon-btn icon-btn--boxed" onClick={() => setAmount((a) => Number(a) + 1)} aria-label="Increase">
            <Icon name="plus" />
          </button>
        </div>

        <p className={`projection ${after < 0 ? 'projection--bad' : ''}`}>
          {product.quantity} on hand <span aria-hidden="true">→</span> <strong>{after}</strong> after this movement
        </p>

        <label className="field">
          <span>Reference (optional)</span>
          <input value={note} onChange={(e) => setNote(e.target.value)} placeholder="PO-2291, order #1182…" maxLength={240} />
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}

        <footer className="dialog__foot">
          <button type="button" className="btn btn--ghost" onClick={onClose}>Cancel</button>
          <button type="submit" className="btn btn--primary" disabled={saving || after < 0 || !Number(amount)}>
            {saving ? 'Recording…' : 'Record movement'}
          </button>
        </footer>
      </form>
    </div>
  );
}
