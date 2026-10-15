import Icon from './Icon.jsx';

const BUILD = import.meta.env.VITE_APP_BUILD || 'dev';

export default function TopBar({ info, online, onAdd }) {
  return (
    <header className="topbar">
      <div className="topbar__inner">
        <a className="brand" href="/" aria-label="Shelfwise home">
          <svg className="brand__mark" viewBox="0 0 32 32" aria-hidden="true">
            <rect x="3" y="6" width="26" height="4" rx="2" />
            <rect x="3" y="14" width="17" height="4" rx="2" className="brand__mid" />
            <rect x="3" y="22" width="22" height="4" rx="2" />
          </svg>
          <span className="brand__name">Shelfwise</span>
        </a>

        <div className="topbar__meta">
          <span className={`conn ${online ? 'conn--up' : 'conn--down'}`}>
            <span className="conn__dot" />
            {online ? `API ${info?.version ?? ''} · ${info?.environment ?? ''}` : 'API offline'}
          </span>
          <span className="build" title="Image tag this frontend was built from">
            build <code>{BUILD.slice(0, 7)}</code>
          </span>
        </div>

        <button type="button" className="btn btn--light" onClick={onAdd}>
          <Icon name="plus" size={16} />
          New product
        </button>
      </div>
    </header>
  );
}
