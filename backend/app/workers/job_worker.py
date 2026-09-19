import asyncio
import os
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from bson import ObjectId
import pymongo
from app.core.config import settings
from app.core.logging_config import logger
from app.db.mongo import DatabaseManager, get_db
from app.services.documents.extractor import extract_document_units
from app.services.documents.chunker import chunk_extracted_units
from app.services.documents.rules import run_deterministic_rules
from app.services.documents.quote_verifier import verify_quote_in_units
from app.services.llm.client import ollama_service
from app.services.url_checks.fetcher import safe_fetch_url, SSRFValidationError
from app.services.url_checks.rules import analyze_url_risk_signals
from app.services.url_checks.official_sources import verify_against_official_sources
from app.services.calculations.loan_calculator import compute_loan_details
from app.schemas.calculations import LoanCalculationRequest
from app.schemas.analyses import EvidenceQuality, ChargeCategory, Severity, ChargeFinding


class JobWorker:
    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.is_running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._current_job_id: Optional[str] = None

    async def start(self):
        self.is_running = True
        logger.info(f"Starting JobWorker [{self.worker_id}]...")
        # 1. Recover abandoned jobs from crashed workers
        await self.recover_abandoned_jobs()
        # 2. Main polling loop
        while self.is_running:
            try:
                job = await self.claim_next_job()
                if job:
                    self._current_job_id = str(job["_id"])
                    await self.process_job(job)
                    self._current_job_id = None
                else:
                    await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)
            except Exception as e:
                logger.error(f"Worker [{self.worker_id}] exception in main loop: {e}")
                await asyncio.sleep(settings.WORKER_POLL_INTERVAL_SECONDS)

    def stop(self):
        self.is_running = False
        logger.info(f"Stopping JobWorker [{self.worker_id}]...")

    async def recover_abandoned_jobs(self):
        """Reset jobs whose leases expired while in 'processing' status."""
        db = get_db()
        now = datetime.now(timezone.utc)
        filter_query = {
            "status": "processing",
            "leaseExpiresAt": {"$lt": now}
        }
        update_query = {
            "$set": {
                "status": "queued",
                "leaseOwner": None,
                "leaseExpiresAt": None,
                "updatedAt": now
            },
            "$inc": {"attemptCount": 1}
        }
        res = await db.jobs.update_many(filter_query, update_query)
        if res.modified_count > 0:
            logger.info(f"Recovered {res.modified_count} abandoned jobs with expired leases.")

    async def claim_next_job(self) -> Optional[Dict[str, Any]]:
        """Atomically claim the oldest queued job using find_one_and_update."""
        db = get_db()
        now = datetime.now(timezone.utc)
        lease_expiration = now + timedelta(seconds=settings.WORKER_LEASE_SECONDS)

        claimed = await db.jobs.find_one_and_update(
            {"status": "queued", "attemptCount": {"$lt": settings.WORKER_MAX_RETRIES}},
            {
                "$set": {
                    "status": "processing",
                    "leaseOwner": self.worker_id,
                    "leaseExpiresAt": lease_expiration,
                    "updatedAt": now
                }
            },
            sort=[("createdAt", pymongo.ASCENDING)],
            return_document=pymongo.ReturnDocument.AFTER
        )
        return claimed

    async def update_job_stage(self, job_id: str, stage: str, status: str = "processing"):
        db = get_db()
        now = datetime.now(timezone.utc)
        lease_expiration = now + timedelta(seconds=settings.WORKER_LEASE_SECONDS)
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "stage": stage,
                    "status": status,
                    "leaseExpiresAt": lease_expiration,
                    "updatedAt": now
                }
            }
        )

    async def process_job(self, job: Dict[str, Any]):
        job_id = str(job["_id"])
        job_type = job.get("type")
        resource_id = job.get("resourceId")
        owner_id = job.get("ownerId")

        logger.info(f"Worker [{self.worker_id}] processing job {job_id} ({job_type})...")

        try:
            if job_type == "document_analysis":
                await self._process_document_analysis(job_id, resource_id, owner_id)
            elif job_type == "url_verification":
                await self._process_url_verification(job_id, resource_id, owner_id)
            else:
                await self._fail_job(job_id, f"Unknown job type: {job_type}")
        except Exception as err:
            logger.error(f"Error executing job {job_id}: {err}", exc_info=True)
            await self._fail_job(job_id, str(err))

    async def _fail_job(self, job_id: str, error_msg: str):
        db = get_db()
        now = datetime.now(timezone.utc)
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "failed",
                    "stage": "failed",
                    "errorCode": error_msg[:200],
                    "updatedAt": now
                }
            }
        )

    async def _process_document_analysis(self, job_id: str, document_id: str, owner_id: str):
        db = get_db()

        # Check if document was deleted or cancelled in the meantime
        doc = await db.documents.find_one({"_id": ObjectId(document_id)})
        if not doc or doc.get("pendingDeletion"):
            logger.info(f"Document {document_id} was deleted or pending deletion. Aborting job {job_id}.")
            await self.update_job_stage(job_id, "cancelled", status="cancelled")
            return

        file_path = os.path.join(settings.UPLOAD_DIRECTORY, doc["storageKey"])
        if not os.path.exists(file_path):
            await self._fail_job(job_id, "Uploaded file not found in storage.")
            return

        # Stage 1: Extracting text
        await self.update_job_stage(job_id, "extracting_text")
        units, quality, warnings = extract_document_units(file_path, doc["detectedMimeType"])

        # Persist chunks into document_chunks collection
        chunks = chunk_extracted_units(units)
        if chunks:
            # Clear old chunks if any
            await db.document_chunks.delete_many({"documentId": document_id})
            chunk_docs = []
            for c in chunks:
                chunk_docs.append({
                    "documentId": document_id,
                    "ownerId": owner_id,
                    "chunkIndex": c.chunk_index,
                    "text": c.text,
                    "sourceReferences": c.source_references,
                    "extractionMethod": c.extraction_method,
                    "extractionWarnings": c.warnings
                })
            await db.document_chunks.insert_many(chunk_docs)

        # Stage 2: Reading financial terms
        await self.update_job_stage(job_id, "reading_financial_terms")
        extracted_terms, deterministic_findings = run_deterministic_rules(units)

        # Stage 3: Checking charges
        await self.update_job_stage(job_id, "checking_charges")

        # Stage 4: Preparing explanation with Ollama
        await self.update_job_stage(job_id, "preparing_explanation")
        
        # Combine text for LLM interpretation (sample up to first 3 chunks)
        combined_sample = "\n\n".join([c.text for c in chunks[:3]])
        llm_findings = []
        is_llm_available = await ollama_service.is_available()

        if is_llm_available and combined_sample:
            try:
                llm_res = await ollama_service.extract_loan_terms(combined_sample)
                if llm_res and "additionalFindings" in llm_res:
                    for f in llm_res["additionalFindings"]:
                        # Verify supporting quote exists in extracted units!
                        quote = f.get("supportingQuote")
                        is_valid_quote, matched_ref = verify_quote_in_units(quote, units)
                        if is_valid_quote:
                            llm_findings.append(ChargeFinding(
                                id=f"finding-{uuid.uuid4().hex[:8]}",
                                title=f.get("title", "Disclosed Clause"),
                                category=f.get("category", ChargeCategory.EASILY_OVERLOOKED),
                                severity=f.get("severity", Severity.LOW),
                                plainLanguageExplanation=f.get("plainLanguageExplanation", ""),
                                amountOrCalculationBasis=f.get("amountOrCalculationBasis"),
                                conditionsUnderWhichItApplies=f.get("conditionsUnderWhichItApplies"),
                                supportingQuote=quote,
                                sourceReference=matched_ref or f.get("sourceReference"),
                                evidenceQuality=EvidenceQuality.CLEAR,
                                recommendedQuestionForLender=f.get("recommendedQuestionForLender", "Ask lender for confirmation in writing.")
                            ))
            except Exception as llm_err:
                logger.warning(f"Ollama extraction skipped: {llm_err}")

        # Merge findings (deterministic + verified LLM findings)
        all_findings = deterministic_findings + llm_findings

        # Calculate estimated loan illustration if loanAmount and interestRate and tenure are available
        calc_result = None
        if (extracted_terms.loanAmount.numericValue and 
            extracted_terms.interestRate.numericValue and 
            extracted_terms.loanTenureMonths.numericValue):
            try:
                from decimal import Decimal
                calc_req = LoanCalculationRequest(
                    loanPrincipal=Decimal(str(extracted_terms.loanAmount.numericValue)),
                    annualInterestRatePercent=Decimal(str(extracted_terms.interestRate.numericValue)),
                    tenureMonths=int(extracted_terms.loanTenureMonths.numericValue)
                )
                calc_response = compute_loan_details(calc_req)
                calc_result = calc_response.model_dump(mode="json")
            except Exception as calc_err:
                logger.warning(f"Calculation illustration failed: {calc_err}")

        # Summary statement
        if len(all_findings) > 0:
            summary_statement = "Additional charges and clauses requiring clarification were identified in the uploaded document."
        else:
            summary_statement = (
                "No additional charges were identified in the readable content. "
                "This does not establish that no other charges apply."
            )

        limitations = list(warnings)
        if not is_llm_available:
            limitations.append("AI explanation unavailable; deterministic rules engine was utilized.")
        if quality == EvidenceQuality.PARTIAL or quality == EvidenceQuality.INSUFFICIENT:
            limitations.append("Some pages had degraded scan quality or required OCR, which may omit faint clauses.")

        # Re-check deletion state before final persistence
        check_doc = await db.documents.find_one({"_id": ObjectId(document_id)})
        if not check_doc or check_doc.get("pendingDeletion"):
            logger.info(f"Document {document_id} was deleted before save. Aborting.")
            return

        now = datetime.now(timezone.utc)
        analysis_doc = {
            "ownerId": owner_id,
            "documentId": document_id,
            "status": "completed",
            "extractedTerms": extracted_terms.model_dump(),
            "findings": [f.model_dump() for f in all_findings],
            "calculations": calc_result,
            "evidenceQuality": quality.value,
            "limitations": limitations,
            "summaryStatement": summary_statement,
            "modelName": settings.OLLAMA_MODEL if is_llm_available else "deterministic-rules-v1",
            "promptVersion": "v1.0.0",
            "analysisVersion": "1.0.0",
            "createdAt": now,
            "completedAt": now
        }

        analysis_res = await db.analyses.insert_one(analysis_doc)

        # Update document record
        await db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {
                "$set": {
                    "extractionStatus": "completed",
                    "latestAnalysisId": str(analysis_res.inserted_id),
                    "pageCount": len(units)
                }
            }
        )

        final_status = "completed_with_limitations" if limitations else "completed"
        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": final_status,
                    "stage": "completed",
                    "resultSummary": {
                        "analysisId": str(analysis_res.inserted_id),
                        "findingsCount": len(all_findings)
                    },
                    "updatedAt": now
                }
            }
        )
        logger.info(f"Document analysis job {job_id} finished ({final_status}).")

    async def _process_url_verification(self, job_id: str, url_check_id: str, owner_id: str):
        db = get_db()
        record = await db.url_checks.find_one({"_id": ObjectId(url_check_id)})
        if not record or record.get("pendingDeletion"):
            await self.update_job_stage(job_id, "cancelled", status="cancelled")
            return

        target_url = record["submittedUrl"]
        await self.update_job_stage(job_id, "fetching_website")

        try:
            fetch_result = await safe_fetch_url(target_url)
        except SSRFValidationError as ssrf_err:
            # Legitimate rejection of unsafe URL
            now = datetime.now(timezone.utc)
            await db.url_checks.update_one(
                {"_id": ObjectId(url_check_id)},
                {
                    "$set": {
                        "overallOutcome": "Significant risk indicators found",
                        "identityVerificationStatus": "Not checked",
                        "limitations": [str(ssrf_err)],
                        "completedAt": now
                    }
                }
            )
            await db.jobs.update_one(
                {"_id": ObjectId(job_id)},
                {
                    "$set": {
                        "status": "failed",
                        "stage": "failed",
                        "errorCode": f"SSRF Protection: {str(ssrf_err)}",
                        "updatedAt": now
                    }
                }
            )
            return

        await self.update_job_stage(job_id, "checking_signals")
        checks, outcome = analyze_url_risk_signals(fetch_result)

        await self.update_job_stage(job_id, "verifying_entity")
        identity_status, claimed_entity, official_check_item = verify_against_official_sources(
            fetch_result.final_url,
            fetch_result.page_title,
            fetch_result.extracted_text
        )
        checks.append(official_check_item)

        await self.update_job_stage(job_id, "preparing_explanation")
        model_summary = None
        if await ollama_service.is_available():
            try:
                model_summary = await ollama_service.summarize_url_evidence(
                    fetch_result.final_url,
                    fetch_result.extracted_text,
                    [c.model_dump() for c in checks]
                )
            except Exception as e:
                logger.warning(f"Ollama URL explanation failed: {e}")

        now = datetime.now(timezone.utc)
        await db.url_checks.update_one(
            {"_id": ObjectId(url_check_id)},
            {
                "$set": {
                    "finalUrl": fetch_result.final_url,
                    "redirectChain": fetch_result.redirect_chain,
                    "claimedEntity": claimed_entity,
                    "overallOutcome": outcome.value,
                    "identityVerificationStatus": identity_status.value,
                    "checks": [c.model_dump() for c in checks],
                    "evidence": {
                        "pageTitle": fetch_result.page_title,
                        "statusCode": fetch_result.status_code,
                        "sampleText": fetch_result.extracted_text[:1000]
                    },
                    "limitations": [
                        "Automated website checks identify visible risk indicators; they do not provide a guarantee of business legitimacy.",
                        "Regulated entity list reflects configured official bank and HFC directory entries."
                    ],
                    "modelSummary": model_summary,
                    "completedAt": now
                }
            }
        )

        await db.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "status": "completed",
                    "stage": "completed",
                    "resultSummary": {"outcome": outcome.value},
                    "updatedAt": now
                }
            }
        )
        logger.info(f"URL check job {job_id} finished ({outcome.value}).")


worker_instance = JobWorker()
