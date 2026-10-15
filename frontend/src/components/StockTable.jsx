import Icon, { StatusBadge } from './Icon.jsx';
import { money, price, units } from '../format.js';

const STATUS_FILTERS = [
  { value: '', label: 'All' },
  { value: 'OK', label: 'Healthy' },
  { value: 'LOW', label: 'Low' },
  { value: 'OUT', label: 'Out' },
];

// The meter shows stock cover: the tick is the reorder point, the full track is 3x that.
function StockMeter({ product }) {
  const capacity = Math.max(product.reorder_level * 3, 1);
  const fill = Math.min(product.quantity / capacity, 1) * 100;
  return (
    <div className="meter" title={`${product.quantity} on hand · reorder at ${product.reorder_level}`}>
      <span className={`meter__fill meter__fill--${product.stock_status.toLowerCase()}`} style={{ width: `${fill}%` }} />
      <span className="meter__tick" />
    </div>
  );
}

export default function StockTable({ products, loading, filters, onFilter, categories, onEdit, onAdjust, onDelete }) {
  return (
    <section className="card ledger" aria-labelledby="ledger-title">
      <div className="ledger__head">
        <div>
          <h2 id="ledger-title" className="card__title">Inventory</h2>
          <p className="muted">{loading ? 'Loading…' : `${products.length} of your products shown`}</p>
        </div>
        <label className="search">
          <Icon name="search" size={16} />
          <input
            type="search"
            placeholder="Search SKU, name or supplier"
            value={filters.q}
            onChange={(e) => onFilter({ q: e.target.value })}
          />
        </label>
      </div>

      <div className="filters">
        <div className="segmented" role="radiogroup" aria-label="Stock status">
          {STATUS_FILTERS.map((f) => (
            <button
              key={f.value || 'all'}
              type="button"
              role="radio"
              aria-checked={filters.status === f.value}
              className={filters.status === f.value ? 'is-active' : ''}
              onClick={() => onFilter({ status: f.value })}
            >
              {f.label}
            </button>
          ))}
        </div>
        <div className="chips" aria-label="Category">
          <button type="button" className={`chip ${!filters.category ? 'is-active' : ''}`} onClick={() => onFilter({ category: '' })}>
            Every category
          </button>
          {categories.map((c) => (
            <button
              key={c}
              type="button"
              className={`chip ${filters.category === c ? 'is-active' : ''}`}
              onClick={() => onFilter({ category: filters.category === c ? '' : c })}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="table-wrap">
        <table className="table">
          <thead>
            <tr>
              <th>SKU · bin</th>
              <th>Product</th>
              <th className="num">On hand</th>
              <th className="col-meter">Cover</th>
              <th className="num">Value</th>
              <th>Status</th>
              <th aria-label="Actions" />
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.id}>
                <td data-label="SKU">
                  <code className="sku">{p.sku}</code>
                  <span className="bin">{p.location || 'no bin'}</span>
                </td>
                <td data-label="Product">
                  <span className="product__name">{p.name}</span>
                  <span className="product__sub">{p.category}{p.supplier ? ` · ${p.supplier}` : ''}</span>
                </td>
                <td data-label="On hand" className="num strong">{units(p.quantity)}</td>
                <td data-label="Cover" className="col-meter"><StockMeter product={p} /></td>
                <td data-label="Value" className="num">
                  <span className="value__total">{money(p.quantity * p.unit_price)}</span>
                  <span className="value__unit">{price(p.unit_price)} each</span>
                </td>
                <td data-label="Status"><StatusBadge status={p.stock_status} /></td>
                <td className="row-actions">
                  <button type="button" className="btn btn--ghost btn--sm" onClick={() => onAdjust(p)} aria-label={`Adjust stock of ${p.name}`}>
                    <Icon name="sliders" size={15} /> Move
                  </button>
                  <button type="button" className="icon-btn" onClick={() => onEdit(p)} aria-label={`Edit ${p.name}`}>
                    <Icon name="edit" size={16} />
                  </button>
                  <button type="button" className="icon-btn icon-btn--danger" onClick={() => onDelete(p)} aria-label={`Delete ${p.name}`}>
                    <Icon name="trash" size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!loading && products.length === 0 && (
          <div className="empty">
            <p className="empty__title">Nothing matches these filters</p>
            <p className="muted">Try another category or clear the search.</p>
          </div>
        )}
      </div>
    </section>
  );
}
