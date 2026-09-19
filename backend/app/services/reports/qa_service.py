from typing import Dict, Any
from app.services.llm.client import ollama_service
from app.schemas.reports import ReportQuestionResponse, CitedSource


async def ask_report_question(
    question: str,
    accessible_report_data: Dict[str, Any]
) -> ReportQuestionResponse:
    """
    Answer a question scoped strictly to the accessible evidence of a report.
    If the LLM is unavailable or Ollama is offline, provides a safe deterministic fallback.
    """
    # 1. Package only accessible terms and findings
    clean_context = {
        "title": accessible_report_data.get("title", "Loan Report"),
        "summary": accessible_report_data.get("summaryStatement") or accessible_report_data.get("modelSummary"),
        "extractedTerms": accessible_report_data.get("extractedTerms"),
        "findings": accessible_report_data.get("findings"),
        "checks": accessible_report_data.get("checks"),
        "limitations": accessible_report_data.get("limitations")
    }

    # 2. Invoke local LLM
    llm_resp = await ollama_service.answer_report_question(question, clean_context)

    cited_sources = []
    if "citedSources" in llm_resp and isinstance(llm_resp["citedSources"], list):
        for cs in llm_resp["citedSources"]:
            if isinstance(cs, dict) and "sourceReference" in cs:
                cited_sources.append(CitedSource(
                    sourceReference=cs.get("sourceReference", "Document"),
                    quote=cs.get("quote")
                ))

    return ReportQuestionResponse(
        question=question,
        answer=llm_resp.get("answer", "Evidence could not be processed at this time."),
        citedSources=cited_sources,
        cannotAnswerReason=llm_resp.get("cannotAnswerReason")
    )
