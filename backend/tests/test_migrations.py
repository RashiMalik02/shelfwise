from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

BACKEND_DIR = Path(__file__).resolve().parents[1]


@pytest.mark.migrations
def test_alembic_upgrade_and_downgrade(tmp_path, monkeypatch):
    from app.config import settings

    url = f"sqlite:///{tmp_path / 'migrations.db'}"
    monkeypatch.setattr(settings, "database_url", url)
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))

    engine = create_engine(url)
    try:
        command.upgrade(cfg, "head")
        assert {"products", "stock_movements", "alembic_version"} <= set(inspect(engine).get_table_names())

        command.downgrade(cfg, "base")
        assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    finally:
        engine.dispose()
