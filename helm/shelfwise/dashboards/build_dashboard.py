"""Generates shelfwise.json. Edit the panels here, then: python3 build_dashboard.py"""

import json
from pathlib import Path

NS = 'namespace="$namespace"'
API = f'{NS}, handler=~"/api.*"'
BLUE = "#2353c8"


def ds():
    return {"type": "prometheus", "uid": "${datasource}"}


def target(expr, legend="", ref="A", instant=False):
    return {"datasource": ds(), "expr": expr, "legendFormat": legend, "refId": ref, "instant": instant}


def stat(pid, title, expr, x, y, unit="none", color=BLUE, thresholds=None, desc=""):
    steps = thresholds or [{"color": color, "value": None}]
    return {
        "id": pid, "type": "stat", "title": title, "description": desc, "datasource": ds(),
        "gridPos": {"h": 4, "w": 4, "x": x, "y": y},
        "targets": [target(expr, instant=True)],
        "fieldConfig": {"defaults": {"unit": unit, "color": {"mode": "thresholds"},
                                     "thresholds": {"mode": "absolute", "steps": steps}}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "colorMode": "background", "graphMode": "none", "textMode": "value", "justifyMode": "center"},
    }


def series(pid, title, targets, x, y, w=12, h=8, unit="short", desc="", stack=False, fixed=None):
    color = {"mode": "fixed", "fixedColor": fixed} if fixed else {"mode": "palette-classic"}
    return {
        "id": pid, "type": "timeseries", "title": title, "description": desc, "datasource": ds(),
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "targets": targets,
        "fieldConfig": {"defaults": {"unit": unit, "color": color, "custom": {
            "lineWidth": 2, "fillOpacity": 12, "showPoints": "never", "spanNulls": True,
            "stacking": {"mode": "normal" if stack else "none", "group": "A"}}}, "overrides": []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "desc"}},
    }


panels = [
    {"id": 100, "type": "row", "title": "Traffic", "collapsed": False, "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0}},
    stat(1, "Requests / s", f"sum(rate(http_requests_total{{{API}}}[1m]))", 0, 1, "reqps",
         desc="All /api requests across every backend replica"),
    stat(2, "p95 latency", f"histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket{{{API}}}[5m])))",
         4, 1, "s", thresholds=[{"color": BLUE, "value": None}, {"color": "#d98a00", "value": 0.3}, {"color": "#c93838", "value": 1}]),
    stat(3, "5xx error rate", f'(sum(rate(http_requests_total{{{API}, status=~"5.."}}[5m])) or vector(0)) / clamp_min(sum(rate(http_requests_total{{{API}}}[5m])), 1e-9)',
         8, 1, "percentunit", thresholds=[{"color": BLUE, "value": None}, {"color": "#c93838", "value": 0.01}]),
    stat(4, "Backend pods", f'count(up{{{NS}, job=~".*backend.*"}} == 1)', 12, 1,
         desc="Backend pods Prometheus is scraping right now"),
    stat(5, "SKUs below reorder point", 'max(shelfwise_products_by_stock_status{status="LOW"})', 16, 1,
         thresholds=[{"color": BLUE, "value": None}, {"color": "#d98a00", "value": 1}]),
    stat(6, "SKUs out of stock", 'max(shelfwise_products_by_stock_status{status="OUT"})', 20, 1,
         thresholds=[{"color": BLUE, "value": None}, {"color": "#c93838", "value": 1}]),
    series(7, "Request rate by endpoint", [target(f"sum by (method, handler) (rate(http_requests_total{{{API}}}[1m]))", "{{method}} {{handler}}")],
           0, 5, unit="reqps"),
    series(8, "Latency by endpoint (p50 / p95)", [
        target(f"histogram_quantile(0.95, sum by (le, handler) (rate(http_request_duration_seconds_bucket{{{API}}}[5m])))", "p95 {{handler}}", "A"),
        target(f"histogram_quantile(0.50, sum by (le) (rate(http_request_duration_seconds_bucket{{{API}}}[5m])))", "p50 all", "B"),
    ], 12, 5, unit="s"),
    series(9, "Responses by status code", [target(f"sum by (status) (rate(http_requests_total{{{API}}}[1m]))", "{{status}}")],
           0, 13, unit="reqps", stack=True),
    series(10, "Stock movements by reason", [target("sum by (reason) (increase(shelfwise_stock_movements_total[5m]))", "{{reason}}")],
           12, 13, unit="short", desc="Counted per replica, then summed"),
    {"id": 101, "type": "row", "title": "Capacity & autoscaling", "collapsed": False, "gridPos": {"h": 1, "w": 24, "x": 0, "y": 21}},
    series(11, "Backend CPU per pod", [target(f'sum by (pod) (rate(container_cpu_usage_seconds_total{{{NS}, container="backend"}}[2m]))', "{{pod}}")],
           0, 22, unit="cores"),
    series(12, "HPA replicas (current vs desired)", [
        target(f'max(kube_horizontalpodautoscaler_status_current_replicas{{{NS}}})', "current", "A"),
        target(f'max(kube_horizontalpodautoscaler_status_desired_replicas{{{NS}}})', "desired", "B"),
        target(f'max(kube_horizontalpodautoscaler_spec_max_replicas{{{NS}}})', "max", "C"),
    ], 12, 22, unit="short"),
    series(13, "Units on hand", [target("max(shelfwise_units_on_hand)", "units")], 0, 30, w=24, h=6, fixed=BLUE),
]

dashboard = {
    "uid": "shelfwise-overview",
    "title": "Shelfwise · API & inventory",
    "tags": ["shelfwise", "fastapi"],
    "timezone": "browser",
    "schemaVersion": 39,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-30m", "to": "now"},
    "templating": {"list": [
        {"name": "datasource", "type": "datasource", "query": "prometheus", "current": {}, "hide": 0, "label": "Data source"},
        {"name": "namespace", "type": "custom", "query": "shelfwise", "current": {"text": "shelfwise", "value": "shelfwise"},
         "options": [{"text": "shelfwise", "value": "shelfwise", "selected": True}], "hide": 0, "label": "Namespace"},
    ]},
    "panels": panels,
}

Path(__file__).with_name("shelfwise.json").write_text(json.dumps(dashboard, indent=2) + "\n")
print("wrote shelfwise.json with", len(panels), "panels")
