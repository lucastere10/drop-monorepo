from pathlib import Path

import pytest
from django.test import override_settings

from core.services.pipeline import load_stored_dataframe
from core.services.storage import LocalStorageBackend


def test_missing_file_with_unique_copy_still_loads(tmp_path: Path):
    root = tmp_path / "uploads"
    root.mkdir()
    kept = root / "abc_pedidos.csv"
    kept.write_text("regiao,valor\nsul,1\nnorte,2\n", encoding="utf-8")
    storage = LocalStorageBackend(root)
    found = storage.find_unique_named("pedidos.csv")
    assert found == kept

    with override_settings(LOCAL_STORAGE_ROOT=root, STORAGE_BACKEND="local"):
        df, _cleaning = load_stored_dataframe(
            "missing_pedidos.csv",
            original_name="pedidos.csv",
        )
    assert list(df.columns) == ["regiao", "valor"]
    assert len(df) == 2


def test_missing_file_without_copy_raises_clear_error(tmp_path: Path):
    root = tmp_path / "uploads"
    root.mkdir()
    with (
        override_settings(LOCAL_STORAGE_ROOT=root, STORAGE_BACKEND="local"),
        pytest.raises(ValueError, match="não está mais disponível"),
    ):
        load_stored_dataframe("gone.csv", original_name="gone.csv")


def test_two_copies_are_not_guessed(tmp_path: Path):
    root = tmp_path / "uploads"
    root.mkdir()
    (root / "a_pedidos.csv").write_text("x\n1\n", encoding="utf-8")
    (root / "b_pedidos.csv").write_text("x\n2\n", encoding="utf-8")
    assert LocalStorageBackend(root).find_unique_named("pedidos.csv") is None
