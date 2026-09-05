from __future__ import annotations

import json

from drop_ai.client import LLMClient
from drop_ai.protocol import Message
from drop_agents.protocol import AgentContext, AgentResult


class PassthroughLLMRunner:
    """Minimal runner: packs summary/tools context and calls LLM once. ADK replaces later."""

    def __init__(self, llm: LLMClient, *, use: str = "chat"):
        self.llm = llm
        self.use = use

    def run(self, ctx: AgentContext) -> AgentResult:
        system_bits = [
            "Você é o assistente Drop. Responda em português do Brasil, de forma clara e objetiva.",
            "Use apenas o contexto do dataset fornecido. Não invente colunas.",
        ]
        if ctx.summary:
            system_bits.append("Resumo do dataset:\n" + json.dumps(ctx.summary, ensure_ascii=False)[:8000])
        if ctx.tools is not None:
            system_bits.append(
                "Schema:\n" + json.dumps(ctx.tools.schema(), ensure_ascii=False)[:4000]
            )
            system_bits.append(
                "Stats:\n" + json.dumps(ctx.tools.stats(), ensure_ascii=False)[:4000]
            )

        messages: list[Message] = [{"role": "system", "content": "\n\n".join(system_bits)}]
        messages.extend(ctx.messages)
        if ctx.goal and (not ctx.messages or ctx.messages[-1].get("content") != ctx.goal):
            messages.append({"role": "user", "content": ctx.goal})

        result = self.llm.complete({"use": self.use, "messages": messages})  # type: ignore[arg-type]
        return AgentResult(
            content=result["content"],
            meta={
                "provider": result["provider"],
                "model": result["model"],
                "input_tokens": result.get("input_tokens"),
                "output_tokens": result.get("output_tokens"),
            },
        )
