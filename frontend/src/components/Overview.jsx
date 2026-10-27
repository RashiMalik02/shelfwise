import { useState } from 'react';
import { money, units } from '../format.js';

const SEGMENTS = [
  { key: 'ok', label: 'Healthy' },
  { key: 'low', label: 'Below reorder point' },
  { key: 'out', label: 'Out of stock' },
];

function HealthStrip({ stats }) {
  const [hover, setHover] = useState(null);
  const counts = {
    out: stats.out_of_stock,
    low: stats.low_stock,
    ok: Math.max(stats.total_skus - stats.low_stock - stats.out_of_stock, 0),
  };
  const total = stats.total_skus || 1;

  return (
    <div className="health">
      <div className="health__head">
        <h2 className="card__title">Stock health</h2>
        <span className="muted">{units(stats.total_skus)} SKUs</span>
      </div>
      <div className="health__bar" role="img" aria-label={SEGMENTS.map((s) => `${s.label} ${counts[s.key]}`).join(', ')}>
        {SEGMENTS.filter((s) => counts[s.key] > 0).map((s) => (
          <span
            key={s.key}
            className={`health__seg health__seg--${s.key}`}
            style={{ flexGrow: counts[s.key] / total }}
            onMouseEnter={() => setHover(s.key)}
            onMouseLeave={() => setHover(null)}
          >
            {hover === s.key && (
              <span className="tip" role="tooltip">
                <strong>{counts[s.key]}</strong> {s.label.toLowerCase()} · {Math.round((counts[s.key] / total) * 100)}%
              </span>
            )}
          </span>
        ))}
        {stats.total_skus === 0 && <span className="health__seg health__seg--empty" />}
      </div>
      <ul className="legend">
        {SEGMENTS.map((s) => (
          <li key={s.key}>
            <span className={`legend__swatch health__seg--${s.key}`} />
            <span className="legend__label">{s.label}</span>
            <span className="legend__value">{counts[s.key]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function Overview({ stats }) {
  const today = new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long' });

  return (
    <section className="overview">
      <div className="overview__band">
        <div className="overview__inner">
          <div className="overview__hero">
            <p className="eyebrow">{today}</p>
            <h1 className="overview__title">Stockroom today</h1>
            <p className="overview__label">Value on the shelves</p>
            <p className="hero-figure">{stats ? money(stats.inventory_value) : '—'}</p>
          </div>
          <div className="card overview__health">{stats ? <HealthStrip stats={stats} /> : <div className="skeleton" />}</div>
        </div>
      </div>

      <div className="tiles">
        <Tile label="Products tracked" value={stats && units(stats.total_skus)} note="distinct SKUs" />
        <Tile label="Units on hand" value={stats && units(stats.total_units)} note="across all bins" />
        <Tile label="Need reordering" value={stats && units(stats.low_stock)} note="at or below reorder point" tone="low" />
        <Tile label="Out of stock" value={stats && units(stats.out_of_stock)} note="cannot be picked" tone="out" />
      </div>
    </section>
  );
}

function Tile({ label, value, note, tone }) {
  return (
    <div className={`tile ${tone ? `tile--${tone}` : ''}`}>
      <p className="tile__label">{label}</p>
      <p className="tile__value">{value ?? '—'}</p>
      <p className="tile__note">{note}</p>
    </div>
  );
}
