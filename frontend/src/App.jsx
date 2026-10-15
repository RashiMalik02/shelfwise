import { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api.js';
import { suggestedReorder } from './format.js';
import Icon from './components/Icon.jsx';
import TopBar from './components/TopBar.jsx';
import Overview from './components/Overview.jsx';
import StockTable from './components/StockTable.jsx';
import { CategoryValue, MovementFeed, ReorderQueue } from './components/SidePanels.jsx';
import { AdjustDialog, ProductDrawer } from './components/Dialogs.jsx';

export default function App() {
  const [info, setInfo] = useState(null);
  const [stats, setStats] = useState(null);
  const [products, setProducts] = useState([]);
  const [reorder, setReorder] = useState([]);
  const [movements, setMovements] = useState([]);
  const [categories, setCategories] = useState([]);
  const [filters, setFilters] = useState({ q: '', category: '', status: '' });
  const [loading, setLoading] = useState(true);
  const [failure, setFailure] = useState('');
  const [drawer, setDrawer] = useState(null); // {} for new, product for edit
  const [adjusting, setAdjusting] = useState(null); // { product, initial }
  const [toast, setToast] = useState(null);
  const toastTimer = useRef();

  const notify = useCallback((message, tone = 'ok') => {
    clearTimeout(toastTimer.current);
    setToast({ message, tone });
    toastTimer.current = setTimeout(() => setToast(null), 3200);
  }, []);

  const loadSummary = useCallback(async () => {
    const [nextInfo, nextStats, nextMoves, nextCats, low, out] = await Promise.all([
      api.info(),
      api.stats(),
      api.movements(10),
      api.categories(),
      api.products({ status: 'LOW' }),
      api.products({ status: 'OUT' }),
    ]);
    setInfo(nextInfo);
    setStats(nextStats);
    setMovements(nextMoves);
    setCategories(nextCats);
    setReorder([...out, ...low]);
  }, []);

  const loadProducts = useCallback(async (f) => {
    setProducts(await api.products(f));
  }, []);

  const refresh = useCallback(async () => {
    try {
      await Promise.all([loadSummary(), loadProducts(filters)]);
      setFailure('');
    } catch (err) {
      setFailure(err.message);
    } finally {
      setLoading(false);
    }
  }, [filters, loadProducts, loadSummary]);

  useEffect(() => {
    // Debounce so typing in the search box doesn't fire a request per keystroke.
    const timer = setTimeout(refresh, filters.q ? 250 : 0);
    return () => clearTimeout(timer);
  }, [refresh, filters.q]);

  const updateFilters = (patch) => setFilters((f) => ({ ...f, ...patch }));

  async function saveProduct(payload, id) {
    if (id) {
      await api.updateProduct(id, payload);
      notify(`Saved ${payload.name}`);
    } else {
      const created = await api.createProduct(payload);
      notify(`${created.sku} added to inventory`);
    }
    setDrawer(null);
    await refresh();
  }

  async function submitAdjustment(id, body) {
    const updated = await api.adjustStock(id, body);
    setAdjusting(null);
    notify(`${updated.sku} now has ${updated.quantity} on hand`);
    await refresh();
  }

  async function removeProduct(product) {
    if (!window.confirm(`Delete ${product.sku} – ${product.name}? Its movement history goes with it.`)) return;
    try {
      await api.deleteProduct(product.id);
      notify(`${product.sku} deleted`, 'neutral');
      await refresh();
    } catch (err) {
      notify(err.message, 'bad');
    }
  }

  return (
    <div className="app">
      <TopBar info={info} online={!failure && Boolean(info)} onAdd={() => setDrawer({})} />

      <Overview stats={stats} />

      <main className="page">
        {failure && (
          <div className="banner" role="alert">
            <Icon name="alert" />
            <div>
              <strong>Can't reach the inventory API.</strong>
              <span> {failure}. Check that the backend pod or container is running.</span>
            </div>
            <button type="button" className="btn btn--ghost btn--sm" onClick={refresh}>
              <Icon name="refresh" size={15} /> Retry
            </button>
          </div>
        )}

        <div className="layout">
          <StockTable
            products={products}
            loading={loading}
            filters={filters}
            onFilter={updateFilters}
            categories={categories}
            onEdit={(p) => setDrawer(p)}
            onAdjust={(p) => setAdjusting({ product: p })}
            onDelete={removeProduct}
          />
          <aside className="side">
            <ReorderQueue
              items={reorder}
              onReceive={(p) => setAdjusting({ product: p, initial: { reason: 'RECEIVED', amount: suggestedReorder(p) } })}
            />
            {stats && stats.categories.length > 0 && <CategoryValue categories={stats.categories} />}
            <MovementFeed movements={movements} />
          </aside>
        </div>
      </main>

      <footer className="footer">
        <span>Shelfwise inventory · FastAPI + PostgreSQL + React</span>
        <a href="/docs" target="_blank" rel="noreferrer">API docs</a>
      </footer>

      {drawer && (
        <ProductDrawer
          key={drawer.id ?? 'new'}
          product={drawer.id ? drawer : null}
          categories={categories}
          onClose={() => setDrawer(null)}
          onSave={saveProduct}
        />
      )}
      {adjusting && (
        <AdjustDialog
          product={adjusting.product}
          initial={adjusting.initial}
          onClose={() => setAdjusting(null)}
          onSubmit={submitAdjustment}
        />
      )}
      {toast && <div className={`toast toast--${toast.tone}`} role="status">{toast.message}</div>}
    </div>
  );
}
