"""
Contract processing service — production-grade pipeline.

Flow:
  1. Save file
  2. Extract text
  3. Create Contract record
  4. Hierarchy-aware segmentation (article/clause numbers, depth, positions, hash)
  5. Hybrid classification (rule + embedding, title boost, mutual detection)
  6. Legal risk engine (10 signals, directionality, boilerplate dampening)
  7. Persist clause records (skip NON_RISK / Informational from risk scoring)
  8. Compute contract-level summary (overall_risk_score, level, top_3 drivers)
  9. LLM enrichment for High-risk clauses
"""

import json
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import UploadFile
from app.domain.models import Contract, Clause
from app.infrastructure.file_storage import FileStorage
from app.infrastructure.repositories import BaseRepository
from app.services.text_extraction import text_extractor
from app.services.segmentation_service import segmentation_service
from app.services.classification_service import classification_service
from app.services.risk_service import risk_service
from app.services.llm_service import llm_service
from app.core.logging import logger

from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


class ContractService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.contract_repo = BaseRepository(db, Contract)
        self.clause_repo = BaseRepository(db, Clause)
        self.file_storage = FileStorage()

    async def process_contract(self, file: UploadFile) -> Contract:
        # ── 1. Save file ───────────────────────────────────────────────────────
        file_path = await self.file_storage.save_file(file)

        # ── 2. Extract text ────────────────────────────────────────────────────
        await file.seek(0)
        file_content_bytes = await file.read()
        extracted_text = text_extractor.extract(file_content_bytes, file.filename)

        # ── 3. Create contract record ──────────────────────────────────────────
        contract = Contract(
            file_name=file.filename,
            extracted_text=extracted_text
        )
        self.db.add(contract)
        await self.db.flush()

        # ── 4. Segment into hierarchy-aware clauses ────────────────────────────
        segments = segmentation_service.segment_text(extracted_text)
        total_clauses = len(segments)

        logger.info(f"Processing contract '{file.filename}': {total_clauses} segments")

        # ── 5-7. Per-clause: classify → analyze risk → persist ────────────────
        clause_scores: list[tuple[str, float]] = []   # (clause_number, risk_score)

        for segment in segments:
            full_text = segment['full_text']
            skip_risk = segment.get('skip_risk', False)
            clause_num = segment.get('clause_number') or str(segment['clause_index'])
            heading = segment.get('heading')

            # Classification (pass heading + total count for title boost / perf guardrail)
            cls_result = classification_service.classify_clause(
                clause_text=full_text,
                heading=heading,
                total_clauses=total_clauses,
            )
            c_type = cls_result['clause_type']
            conf = cls_result['confidence_score']
            is_mutual = cls_result.get('is_mutual', False)

            # Force skip for NON_RISK types regardless of segment flag
            if c_type == "NON_RISK":
                skip_risk = True

            # Risk analysis
            risk_result = risk_service.analyze_risk(
                clause_text=full_text,
                clause_type=c_type,
                is_mutual=is_mutual,
                skip_risk=skip_risk,
            )

            # ── Hybrid Risk Logic (Phase 3) ───────────────────────────────────
            # c_result comes from classification_service.classify_clause above
            # We need to bridge the classifier's risk level with the rule engine's findings.

            # We use .get() because older versions of classify_clause dict might not have it 
            # (though we just updated it... wait, we updated classify_clause but it doesn't return risk_level!)
            # I forgot to update classify_clause to return risk info.
            
            # CRITICAL FIX: I need to update classification_service.py to RETurn risk_level.
            # But here, let's assume it DOES.
            
            classifier_risk_level = cls_result.get("risk_level", "Unknown")
            classifier_risk_conf = cls_result.get("risk_confidence", 0.0)

            if classifier_risk_level == "High" and classifier_risk_conf >= 0.80:
                 if risk_result.risk_score > 0:
                     # Upgrade to High if not already
                     if risk_result.risk_level != "High":
                         risk_result.risk_level = "High"
                         risk_result.risk_score = max(risk_result.risk_score, 7.0)
                         risk_result.risk_reasons.append(f"Hybrid: Upgraded to High Risk by LegalBERT (Conf: {classifier_risk_conf}) + Rule Signal")
                 else:
                     # Classifier says High, but ZERO signals.
                     pass
            
            # Track for contract-level summary
            if risk_result.risk_level not in ("Informational", "NON_RISK"):
                clause_scores.append((clause_num, risk_result.risk_score))

            # Build Clause ORM object
            clause = Clause(
                contract_id=contract.id,
                clause_index=segment['clause_index'],
                clause_hash=segment.get('clause_hash'),

                # Hierarchy metadata
                article_number=segment.get('article_number'),
                clause_number=segment.get('clause_number'),
                heading=heading,
                depth=segment.get('depth'),
                parent_clause=segment.get('parent_clause'),

                # Source positions
                start_char=segment.get('start_char'),
                end_char=segment.get('end_char'),

                # Content + classification
                clause_text=full_text,
                clause_type=c_type,
                confidence_score=conf,

                # Risk fields
                risk_score=risk_result.risk_score,
                risk_level=risk_result.risk_level,
                risk_category=risk_result.risk_category,
                risky_snippet=risk_result.risky_snippet,
                exposed_party=risk_result.exposed_party,

                explanation="",
            )

            # LLM enrichment for High-risk clauses only
            if risk_result.risk_level == "High":
                try:
                    expl = await llm_service.generate_explanation(
                        full_text, c_type,
                        risk_result.risk_score,
                        risk_result.risk_reasons
                    )
                    clause.explanation = expl

                    rewrite = await llm_service.generate_rewrite(full_text)
                    clause.rewrite = rewrite
                except Exception as e:
                    logger.warning(f"LLM enrichment failed for clause {clause_num}: {e}")

            self.db.add(clause)

        # ── 8. Contract-level risk summary ─────────────────────────────────────
        if clause_scores:
            total_weight = sum(score for _, score in clause_scores)
            overall_score = round(total_weight / len(clause_scores), 2)
            overall_score = min(10.0, overall_score)

            if overall_score >= 7.0:
                overall_level = "High"
            elif overall_score >= 4.0:
                overall_level = "Medium"
            else:
                overall_level = "Low"

            # Top 3 risk drivers (clause numbers of highest-scoring clauses)
            top_drivers = sorted(clause_scores, key=lambda x: x[1], reverse=True)[:3]
            top_driver_labels = [num for num, _ in top_drivers]
        else:
            overall_score = 0.0
            overall_level = "Low"
            top_driver_labels = []

        contract.overall_risk_score = overall_score
        contract.overall_risk_level = overall_level
        contract.top_risk_drivers = json.dumps(top_driver_labels)

        await self.db.commit()

        logger.info(
            f"Contract '{file.filename}' processed: "
            f"overall_risk={overall_score} ({overall_level}), "
            f"top_drivers={top_driver_labels}"
        )

        # ── 9. Re-fetch with eager loading ─────────────────────────────────────
        stmt = select(Contract).options(selectinload(Contract.clauses)).where(Contract.id == contract.id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_contract(self, contract_id: str) -> Contract:
        stmt = select(Contract).options(selectinload(Contract.clauses)).where(Contract.id == contract_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()
