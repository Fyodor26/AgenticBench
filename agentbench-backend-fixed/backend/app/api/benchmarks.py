from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.dependencies import get_db
from app.models.user import User
from app.schemas.benchmark import (
    BenchmarkCreate,
    BenchmarkResponse,
)
from app.services.benchmark_service import (
    BenchmarkService,
)
from app.schemas.benchmark import BenchmarkRunRequest
router = APIRouter(
    prefix="/benchmarks",
    tags=["Benchmarks"],
)


@router.post(
    "",
    response_model=BenchmarkResponse,
)
def create_benchmark(
    benchmark: BenchmarkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return BenchmarkService.create(
        db,
        benchmark,
        current_user.id,
    )


@router.get(
    "",
    response_model=list[BenchmarkResponse],
)
def list_benchmarks(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return BenchmarkService.get_all(
        db,
        current_user.id,
    )

@router.post("/run")
async def run_benchmark(
    request: BenchmarkRunRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await BenchmarkService.run(
    db=db,
    request=request,
    user_id=current_user.id,
)
@router.get("/{benchmark_id}/results")
def get_results(
    benchmark_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BenchmarkService.get_results(
        db,
        benchmark_id,
        current_user.id,
    )