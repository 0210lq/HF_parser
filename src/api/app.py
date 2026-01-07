"""
FastAPI application for HF Parser
"""
from datetime import date
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from loguru import logger

from src.database import connection, queries
from src.database.models import VALID_PERFORMANCE_FIELDS

# Create FastAPI app
app = FastAPI(
    title="HF Parser API",
    description="Private Fund Weekly Report Parser API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== Dependency =====

def get_db() -> Session:
    """Database session dependency"""
    with connection.get_session() as session:
        yield session


# ===== Response Models =====

class StatsResponse(BaseModel):
    """System statistics response"""
    total_managers: int
    total_strategies: int
    total_funds: int
    total_performances: int
    latest_report_date: Optional[str]


class ReportDatesResponse(BaseModel):
    """Available report dates response"""
    dates: List[str]


class RankingItem(BaseModel):
    """Ranking item"""
    rank: int
    fund_code: str
    fund_name: str
    manager_name: Optional[str]
    strategy_name: Optional[str]
    value: Optional[float]
    report_date: str


class RankingResponse(BaseModel):
    """Performance ranking response"""
    metric: str
    report_date: str
    items: List[RankingItem]
    total: int


class StrategyDistributionItem(BaseModel):
    """Strategy distribution item"""
    level1_category: str
    level2_category: str
    level3_category: str
    fund_count: int


class FundSearchResponse(BaseModel):
    """Fund search response"""
    items: List[dict]
    total: int


class StrategyItem(BaseModel):
    """Strategy item"""
    strategy_id: int
    level1_category: str
    level2_category: str
    level3_category: str


class ManagerItem(BaseModel):
    """Manager item"""
    manager_id: int
    manager_name: str
    establishment_date: Optional[str]
    company_size: Optional[str]


# ===== Health Check =====

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_ok = connection.check_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected"
    }


# ===== Analytics Endpoints =====

@app.get("/api/analytics/stats", response_model=StatsResponse)
async def get_stats(
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get system statistics"""
    try:
        report_date_obj = date.fromisoformat(report_date) if report_date else None
        stats = queries.get_system_stats(db, report_date_obj)
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/report-dates", response_model=ReportDatesResponse)
async def get_report_dates(db: Session = Depends(get_db)):
    """Get available report dates"""
    try:
        dates = queries.get_available_report_dates(db)
        return {"dates": dates}
    except Exception as e:
        logger.error(f"Error getting report dates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/ranking", response_model=RankingResponse)
async def get_ranking(
    metric: str = Query("annual_return", description="Performance metric"),
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    strategy_id: Optional[int] = Query(None, description="Strategy ID filter"),
    manager_id: Optional[int] = Query(None, description="Manager ID filter"),
    limit: int = Query(50, ge=1, le=200, description="Number of results (1-200)"),
    db: Session = Depends(get_db)
):
    """Get performance ranking by metric"""
    try:
        # Validate metric
        if metric not in VALID_PERFORMANCE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric. Valid metrics: {', '.join(sorted(VALID_PERFORMANCE_FIELDS))}"
            )

        report_date_obj = date.fromisoformat(report_date) if report_date else None
        items = queries.get_performance_ranking(
            db,
            metric=metric,
            report_date=report_date_obj,
            strategy_id=strategy_id,
            manager_id=manager_id,
            limit=limit
        )

        # Get actual report date used
        actual_report_date = items[0]['report_date'] if items else None

        return {
            "metric": metric,
            "report_date": actual_report_date or "",
            "items": items,
            "total": len(items)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ranking: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/analytics/strategy-distribution", response_model=List[StrategyDistributionItem])
async def get_strategy_distribution(
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get fund count distribution by strategy"""
    try:
        report_date_obj = date.fromisoformat(report_date) if report_date else None
        distribution = queries.get_strategy_distribution(db, report_date_obj)
        return distribution
    except Exception as e:
        logger.error(f"Error getting strategy distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Fund Endpoints =====

@app.get("/api/funds", response_model=FundSearchResponse)
async def search_funds(
    keyword: Optional[str] = Query(None, description="Search keyword (fund or manager name)"),
    strategy_id: Optional[int] = Query(None, description="Strategy ID filter"),
    manager_id: Optional[int] = Query(None, description="Manager ID filter"),
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    sort_by: str = Query("annual_return", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit (1-100)"),
    db: Session = Depends(get_db)
):
    """Search funds with filters and pagination"""
    try:
        # Validate sort_by
        if sort_by not in VALID_PERFORMANCE_FIELDS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by field. Valid fields: {', '.join(sorted(VALID_PERFORMANCE_FIELDS))}"
            )

        report_date_obj = date.fromisoformat(report_date) if report_date else None
        result = queries.search_funds(
            db,
            keyword=keyword,
            strategy_id=strategy_id,
            manager_id=manager_id,
            report_date=report_date_obj,
            sort_by=sort_by,
            sort_order=sort_order,
            offset=offset,
            limit=limit
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching funds: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/funds/{fund_code}")
async def get_fund_detail(
    fund_code: str,
    report_date: Optional[str] = Query(None, description="Report date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get detailed information for a specific fund"""
    try:
        report_date_obj = date.fromisoformat(report_date) if report_date else None
        detail = queries.get_fund_detail(db, fund_code, report_date_obj)

        if not detail:
            raise HTTPException(status_code=404, detail=f"Fund not found: {fund_code}")

        return detail
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fund detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Strategy Endpoints =====

@app.get("/api/strategies", response_model=List[StrategyItem])
async def get_strategies(db: Session = Depends(get_db)):
    """Get all strategies"""
    try:
        strategies = queries.get_all_strategies(db)
        return strategies
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Manager Endpoints =====

@app.get("/api/managers", response_model=List[ManagerItem])
async def get_managers(
    limit: int = Query(1000, ge=1, le=10000, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """Get all managers"""
    try:
        managers = queries.get_all_managers(db, limit=limit)
        return managers
    except Exception as e:
        logger.error(f"Error getting managers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Root Endpoint =====

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "HF Parser API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
