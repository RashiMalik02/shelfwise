import { useState } from 'react';
import Icon, { StatusBadge } from './Icon.jsx';
import { compactMoney, money, suggestedReorder, timeAgo, units } from '../format.js';

export function ReorderQueue({ items, onReceive }) {
  return (
    <section className="card panel" aria-labelledby="reorder-title">
      <div className="panel__head">
        <h2 id="reorder-title" className="card__title">Reorder queue</h2>
        <span className="count-pill">{items.length}</span>
      </div>
      {items.length === 0 ? (
        <p className="muted panel__empty">Every product is above its reorder point.</p>
      ) : (
        <ul className="queue">
          {items.map((p) => (
            <li key={p.id} className="queue__item">
              <div className="queue__text">
                <span className="queue__name">{p.name}</span>
                <span className="queue__meta">
                  <code>{p.sku}</code> · {p.quantity} left, reorder at {p.reorder_level}
                </span>
              </div>
              <div className="queue__side">
                <StatusBadge status={p.stock_status} />
                <button type="button" className="btn btn--primary btn--sm" onClick={() => onReceive(p)}>
                  Receive {suggestedReorder(p)}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function CategoryValue({ categories }) {
  const [hover, setHover] = useState(null);
  const max = Math.max(...categories.map((c) => c.value), 1);
  return (
    <section className="card panel" aria-labelledby="cat-title">
      <div className="panel__head">
        <h2 id="cat-title" className="card__title">Value by category</h2>
      </div>
      <ul className="bars">
        {categories.map((c) => (
          <li
            key={c.category}
            className="bars__row"
            onMouseEnter={() => setHover(c.category)}
            onMouseLeave={() => setHover(null)}
          >
            <span className="bars__label">{c.category}</span>
            <span className="bars__track">
              <span className="bars__fill" style={{ width: `${Math.max((c.value / max) * 100, 2)}%` }} />
              <span className="bars__value">{compactMoney(c.value)}</span>
              {hover === c.category && (
                <span className="tip" role="tooltip">
                  <strong>{money(c.value)}</strong> · {c.skus} SKUs · {units(c.units)} units
                </span>
              )}
            </span>
          </li>
        ))}
      </ul>
      <details className="table-view">
        <summary>View as table</summary>
        <table className="table table--compact">
          <thead>
            <tr><th>Category</th><th className="num">SKUs</th><th className="num">Units</th><th className="num">Value</th></tr>
          </thead>
          <tbody>
            {categories.map((c) => (
              <tr key={c.category}>
                <td>{c.category}</td><td className="num">{c.skus}</td><td className="num">{units(c.units)}</td><td className="num">{money(c.value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </section>
  );
}

const REASON_LABEL = { RECEIVED: 'Received', SOLD: 'Picked / sold', RETURNED: 'Returned', DAMAGED: 'Written off', COUNT: 'Stock count' };

export function MovementFeed({ movements }) {
  return (
    <section className="card panel" aria-labelledby="moves-title">
      <div className="panel__head">
        <h2 id="moves-title" className="card__title">Stock movements</h2>
        <span className="muted">latest {movements.length}</span>
      </div>
      <ol className="moves">
        {movements.map((m) => (
          <li key={m.id} className="moves__item">
            <span className={`moves__icon ${m.delta > 0 ? 'is-in' : 'is-out'}`}>
              <Icon name={m.delta > 0 ? 'inbound' : 'outbound'} size={15} />
            </span>
            <div className="moves__text">
              <span>
                <strong>{m.delta > 0 ? `+${m.delta}` : m.delta}</strong> {m.product_name}
              </span>
              <span className="moves__meta">
                {REASON_LABEL[m.reason] ?? m.reason}
                {m.note ? ` · ${m.note}` : ''} · now {m.quantity_after}
              </span>
            </div>
            <time className="moves__time" dateTime={m.created_at}>{timeAgo(m.created_at)}</time>
          </li>
        ))}
      </ol>
    </section>
  );
}
