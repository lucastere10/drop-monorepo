from __future__ import annotations

import json
import logging

from django.db import transaction
from drop_agents import PassthroughLLMRunner
from drop_ai.protocol import Message as LLMMessage

from accounts.services.credits import refund
from core.models import Analysis, ChartSpec, Insight, Message
from core.services.tools import AnalysisTools
from workers.models import Job
from workers.services.llm_factory import get_llm_client

logger = logging.getLogger(__name__)


def run_job(job_id: str) -> None:
    with transaction.atomic():
        # of=("self",): Postgres forbids FOR UPDATE on nullable outer joins (Job.user).
        job = Job.objects.select_for_update(of=("self",)).get(pk=job_id)
        if job.status in {Job.Status.SUCCEEDED, Job.Status.RUNNING}:
            return
        job.status = Job.Status.RUNNING
        job.save(update_fields=["status", "updated_at"])

    try:
        result = _execute(job)
        job.refresh_from_db()
        if job.status == Job.Status.SUCCEEDED:
            return
        job.status = Job.Status.SUCCEEDED
        job.result = result
        job.save(update_fields=["status", "result", "updated_at"])
    except Exception as exc:
        logger.exception("job failed id=%s", job_id)
        job.refresh_from_db()
        job.status = Job.Status.FAILED
        job.error = str(exc)
        job.save(update_fields=["status", "error", "updated_at"])
        if job.job_type == "ai_dashboard" and job.analysis_id:
            Analysis.objects.filter(pk=job.analysis_id).update(dashboard_job_id=None)
        if job.credits_debited and not job.credits_refunded and job.credit_action and job.user_id:
            refund(job.user, action=job.credit_action, reference_id=str(job.id))
            job.credits_refunded = True
            job.save(update_fields=["credits_refunded", "updated_at"])


def _execute(job: Job) -> dict:
    handlers = {
        "ai_overview": handle_overview,
        "ai_insights": handle_insights,
        "ai_chat": handle_chat,
        "ai_charts": handle_charts,
        "ai_dashboard": handle_dashboard,
        "cron_renew_credits": handle_cron_renew,
        "cron_cleanup_uploads": handle_cron_cleanup,
    }
    handler = handlers.get(job.job_type)
    if handler is None:
        raise ValueError(f"Unknown job type: {job.job_type}")
    return handler(job)


def handle_overview(job: Job) -> dict:
    analysis = _analysis(job)
    llm = get_llm_client()
    raw = analysis.summary or {}
    outliers = raw.get("outliers") or {}
    top_outliers = dict(
        sorted(outliers.items(), key=lambda x: x[1].get("count", 0), reverse=True)[:5]
    )
    payload = {
        "title": analysis.title,
        "n_rows": raw.get("n_rows"),
        "n_cols": raw.get("n_cols"),
        "quality": raw.get("quality"),
        "missing_pct": raw.get("missing_pct"),
        "duplicates": raw.get("duplicates"),
        "outliers_top": top_outliers,
        "schema": (raw.get("schema") or [])[:40],
        "numeric_stats": dict(list((raw.get("numeric_stats") or {}).items())[:15]),
        "correlations": dict(list((raw.get("correlations") or {}).items())[:10]),
        "categorical_top": dict(list((raw.get("categorical_top") or {}).items())[:8]),
        "cleaning": raw.get("cleaning") or {},
    }
    messages: list[LLMMessage] = [
        {
            "role": "system",
            "content": (
                "Você escreve resumos executivos em português do Brasil para gestores, "
                "não para engenheiros de dados. "
                "Produza Markdown com EXATAMENTE estas seções (##):\n"
                "1. Em uma frase — o que o arquivo parece ser\n"
                "2. Qualidade — em linguagem simples (campos vazios, linhas repetidas, "
                "valores extremos); mencione a nota/grade de forma suave\n"
                "3. Pontos positivos — 2 a 4 bullets do que já dá para confiar ou explorar\n"
                "4. A explorar — 2 a 4 bullets de riscos ou lacunas (sem jargão técnico)\n"
                "5. Decisões / próximos passos — 2 a 3 perguntas ou ações concretas\n\n"
                "Evite termos como completeness, uniqueness, consistency, dtype, schema. "
                "Prefira: campos vazios, linhas repetidas, valores extremos. "
                "Limite: cerca de 350 palavras. Tom direto, sem emoji, sem enrolação. "
                "Não invente colunas ou estatísticas ausentes do contexto."
            ),
        },
        {
            "role": "user",
            "content": "Contexto do dataset (JSON):\n"
            + json.dumps(payload, ensure_ascii=False)[:14000],
        },
    ]
    result = llm.complete({"use": "overview", "messages": messages, "max_tokens": 2048})
    analysis.overview_text = result["content"]
    analysis.save(update_fields=["overview_text", "updated_at"])
    column_labels = _column_labels(llm, analysis)
    return {
        "overview": result["content"],
        "column_labels": column_labels,
        "meta": {"provider": result["provider"], "model": result["model"]},
    }


def handle_insights(job: Job) -> dict:
    analysis = _analysis(job)
    llm = get_llm_client()
    tools = AnalysisTools(analysis)
    messages: list[LLMMessage] = [
        {
            "role": "system",
            "content": "Gere 3 a 5 insights acionáveis em markdown (pt-BR) sobre o dataset.",
        },
        {
            "role": "user",
            "content": json.dumps(
                {"stats": tools.stats(), "schema": tools.schema(), "sample": tools.sample(5)},
                ensure_ascii=False,
            )[:12000],
        },
    ]
    result = llm.complete({"use": "insights", "messages": messages})
    insight = Insight.objects.create(
        analysis=analysis,
        kind="general",
        content=result["content"],
        meta={"provider": result["provider"], "model": result["model"]},
    )
    return {"insight_id": str(insight.id), "content": result["content"]}


def handle_chat(job: Job) -> dict:
    from core.services.conversations import resolve_conversation

    analysis = _analysis(job)
    question = (job.payload or {}).get("message") or (job.payload or {}).get("question") or ""
    if not question:
        raise ValueError("message is required")
    conversation_id = (job.payload or {}).get("conversation_id")
    conversation = resolve_conversation(analysis, conversation_id)

    Message.objects.create(conversation=conversation, role=Message.Role.USER, content=question)
    history = list(conversation.messages.order_by("created_at").values("role", "content")[:20])
    llm_messages: list[LLMMessage] = [
        {"role": m["role"], "content": m["content"]}  # type: ignore[misc]
        for m in history
        if m["role"] in {"user", "assistant", "system"}
    ]
    runner = PassthroughLLMRunner(
        get_llm_client(),
        use="chat",
        system_extra=(
            "Responda APENAS JSON válido: "
            '{"answer": str, "charts": [intenção ou lista vazia]}. '
            "charts tem 0 ou 1 item. Intenção: title, description, "
            'chart_type "bar"|"line"|"pie", '
            'kind "categorical_top"|"histogram"|"timeseries"|"groupby"|"correlation", '
            "columns (nomes reais do schema), agg count|mean|sum. "
            "Não inclua labels nem values. "
            "Se a pergunta não pedir visualização, use charts: []."
        ),
        response_format={"type": "json_object"},
    )
    from drop_agents.protocol import AgentContext

    agent_result = runner.run(
        AgentContext(
            analysis_id=analysis.id,
            goal=question,
            messages=llm_messages[:-1] if llm_messages else [],
            tools=AnalysisTools(analysis),
            summary={k: v for k, v in (analysis.summary or {}).items() if k != "sample_rows"},
        )
    )
    from core.services.chart_compiler import materialize_chart_intents
    from core.services.chart_planner import parse_chat_response

    answer, intents = parse_chat_response(agent_result.content)
    charts = materialize_chart_intents(analysis, intents, source="chat") if intents else []
    chart_ids = [str(c.id) for c in charts]
    Message.objects.create(
        conversation=conversation,
        role=Message.Role.ASSISTANT,
        content=answer,
        meta={"chart_ids": chart_ids} if chart_ids else {},
    )
    return {
        "conversation_id": str(conversation.id),
        "answer": answer,
        "charts": [_chart_payload(c) for c in charts],
        "meta": agent_result.meta,
    }


def handle_charts(job: Job) -> dict:
    analysis = _analysis(job)
    charts = _compile_planned(analysis, min_charts=1, max_charts=1, source="llm")
    chart = charts[0]
    from core.services.dashboard_layout import append_chart_to_layout

    analysis.dashboard_layout = append_chart_to_layout(
        analysis.dashboard_layout,
        chart_id=str(chart.id),
        chart_type=chart.chart_type,
    )
    analysis.save(update_fields=["dashboard_layout", "updated_at"])
    return {
        "chart_id": str(chart.id),
        "spec": chart.spec,
        "dashboard_layout": analysis.dashboard_layout,
    }


def handle_dashboard(job: Job) -> dict:
    analysis = _analysis(job)
    charts = _compile_planned(analysis, min_charts=6, max_charts=8, source="llm")
    from core.services.dashboard_layout import build_dashboard_layout

    layout = build_dashboard_layout([(str(c.id), c.chart_type) for c in charts])
    analysis.dashboard_layout = layout
    analysis.dashboard_job_id = None
    analysis.save(update_fields=["dashboard_layout", "dashboard_job_id", "updated_at"])
    return {
        "charts": [_chart_payload(c) for c in charts],
        "dashboard_layout": layout,
    }


def handle_cron_renew(job: Job) -> dict:
    from io import StringIO

    from django.core.management import call_command

    out = StringIO()
    call_command("renew_credits", stdout=out)
    return {"log": out.getvalue()}


def handle_cron_cleanup(job: Job) -> dict:
    from core.services.cleanup import cleanup_expired_uploads

    deleted = cleanup_expired_uploads()
    return {"deleted": deleted}



def _compile_planned(analysis: Analysis, *, min_charts: int, max_charts: int, source: str) -> list[ChartSpec]:
    from core.services.chart_compiler import materialize_chart_intents
    from core.services.chart_planner import plan_chart_intents

    intents = plan_chart_intents(
        get_llm_client(),
        analysis,
        min_charts=min_charts,
        max_charts=max_charts,
    )
    charts = materialize_chart_intents(analysis, intents, source=source)
    if not charts:
        raise ValueError("Nenhum gráfico válido a partir do plano")
    return charts


def _chart_payload(chart: ChartSpec) -> dict:
    return {
        "id": str(chart.id),
        "title": chart.title,
        "chart_type": chart.chart_type,
        "spec": chart.spec,
        "created_at": chart.created_at.isoformat(),
    }


def _column_labels(llm, analysis: Analysis) -> dict:
    from core.services.column_labels import assign_column_labels

    try:
        return assign_column_labels(llm, analysis)
    except Exception:
        logger.exception("column labels failed analysis=%s", analysis.id)
        return {}


def _analysis(job: Job) -> Analysis:
    analysis_id = (job.payload or {}).get("analysis_id") or (job.analysis_id and str(job.analysis_id))
    analysis = Analysis.objects.filter(pk=analysis_id).first()
    if analysis is None:
        raise ValueError("analysis not found")
    if analysis.is_expired:
        raise ValueError("analysis expired")
    if job.user_id and analysis.user_id and analysis.user_id != job.user_id:
        raise ValueError("analysis not found")
    return analysis
