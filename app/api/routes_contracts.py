from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.infrastructure.database import get_db
from app.services.contract_service import ContractService
from app.domain.models import Contract

router = APIRouter()


@router.get("/")
async def list_contracts(db: AsyncSession = Depends(get_db)):
    """Return all contracts as lightweight summaries (no extracted_text or full clauses)."""
    result = await db.execute(
        select(Contract)
        .options(selectinload(Contract.clauses))
        .order_by(Contract.upload_time.desc())
    )
    contracts = result.scalars().all()

    return [
        {
            "id": c.id,
            "file_name": c.file_name,
            "upload_time": c.upload_time.isoformat() if c.upload_time else None,
            "overall_risk_score": c.overall_risk_score,
            "overall_risk_level": c.overall_risk_level,
            "top_risk_drivers": c.top_risk_drivers,
            "clause_count": len(c.clauses),
        }
        for c in contracts
    ]


@router.post("/upload")
async def upload_contract(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    service = ContractService(db)
    try:
        contract = await service.process_contract(file)
        return {"contract_id": contract.id, "message": "Contract processed successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{contract_id}")
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    service = ContractService(db)
    contract = await service.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    return contract
