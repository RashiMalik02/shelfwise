"""Business metrics exposed next to the standard HTTP metrics on /metrics."""

import logging

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.registry import Collector
from sqlalchemy import case, func, select

from .database import SessionLocal
from .models import Product

log = logging.getLogger(__name__)

STOCK_MOVEMENTS = Counter(
    "shelfwise_stock_movements_total",
    "Stock movements recorded, split by reason",
    ["reason"],
)


class InventoryCollector(Collector):
    """Reads current inventory levels from Postgres on every scrape.

    Every backend replica reports the same numbers, so dashboards should use
    max() rather than sum() on these gauges.
    """

    def collect(self):
        try:
            with SessionLocal() as db:
                skus, units, low, out = db.execute(
                    select(
                        func.count(Product.id),
                        func.coalesce(func.sum(Product.quantity), 0),
                        func.coalesce(
                            func.sum(
                                case(((Product.quantity > 0) & (Product.quantity <= Product.reorder_level), 1), else_=0)
                            ),
                            0,
                        ),
                        func.coalesce(func.sum(case((Product.quantity == 0, 1), else_=0)), 0),
                    )
                ).one()
        except Exception:  # the DB being down must never break /metrics
            log.warning("inventory collector could not reach the database", exc_info=True)
            return

        yield GaugeMetricFamily("shelfwise_products", "Number of SKUs in the catalogue", value=skus)
        yield GaugeMetricFamily("shelfwise_units_on_hand", "Total units across all SKUs", value=units)
        stock = GaugeMetricFamily("shelfwise_products_by_stock_status", "SKUs per stock status", labels=["status"])
        stock.add_metric(["LOW"], low)
        stock.add_metric(["OUT"], out)
        stock.add_metric(["OK"], skus - low - out)
        yield stock


_registered = False


def register_inventory_collector() -> None:
    global _registered
    if not _registered:
        REGISTRY.register(InventoryCollector())
        _registered = True
