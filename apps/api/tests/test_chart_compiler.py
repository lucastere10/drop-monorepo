import pandas as pd

from core.services.chart_compiler import compile_intent


def test_compile_ignores_model_values_and_uses_counts():
    df = pd.DataFrame({"regiao": ["sul", "sul", "norte", "norte", "norte"]})
    intent = {
        "title": "Pedidos por região",
        "description": "contagem",
        "chart_type": "bar",
        "kind": "groupby",
        "columns": ["regiao"],
        "agg": "count",
        "labels": ["inventado"],
        "values": [999],
    }
    payload = compile_intent(df, {}, intent)
    assert payload is not None
    assert payload["spec"]["labels"] == ["norte", "sul"]
    assert payload["spec"]["values"] == [3.0, 2.0]
    assert 999 not in payload["spec"]["values"]
    assert "inventado" not in payload["spec"]["labels"]


def test_compile_rejects_unknown_column():
    df = pd.DataFrame({"regiao": ["sul", "norte"]})
    payload = compile_intent(
        df,
        {},
        {
            "title": "Fantasma",
            "kind": "categorical_top",
            "columns": ["nao_existe"],
            "chart_type": "bar",
            "agg": "count",
        },
    )
    assert payload is None


def test_groupby_mean_uses_real_numbers():
    df = pd.DataFrame(
        {
            "loja": ["a", "a", "b", "b"],
            "valor": [10, 20, 5, 7],
        }
    )
    payload = compile_intent(
        df,
        {},
        {
            "title": "Ticket por loja",
            "kind": "groupby",
            "columns": ["loja", "valor"],
            "agg": "mean",
            "chart_type": "bar",
        },
    )
    assert payload is not None
    assert payload["spec"]["labels"][0] == "a"
    assert payload["spec"]["values"][0] == 15.0
