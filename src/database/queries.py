"""
Database query functions
"""
from datetime import date
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy import func, desc, asc, or_, and_
from sqlalchemy.orm import Session, joinedload
from loguru import logger

from .models import Manager, Strategy, Fund, FundPerformance, ReportMetadata, VALID_PERFORMANCE_FIELDS


# ===== Analytics Queries =====

def get_system_stats(session: Session, report_date: Optional[date] = None) -> Dict[str, Any]:
    """Get system statistics

    Args:
        session: Database session
        report_date: Optional report date filter

    Returns:
        Dictionary with system statistics
    """
    stats = {}

    # Total managers
    stats['total_managers'] = session.query(Manager).count()

    # Total strategies
    stats['total_strategies'] = session.query(Strategy).count()

    # Total funds
    stats['total_funds'] = session.query(Fund).count()

    # Total performances
    if report_date:
        stats['total_performances'] = session.query(FundPerformance).filter(
            FundPerformance.report_date == report_date
        ).count()
    else:
        stats['total_performances'] = session.query(FundPerformance).count()

    # Latest report date
    latest = session.query(func.max(FundPerformance.report_date)).scalar()
    stats['latest_report_date'] = latest.isoformat() if latest else None

    return stats


def get_available_report_dates(session: Session) -> List[str]:
    """Get list of available report dates

    Args:
        session: Database session

    Returns:
        List of report dates (ISO format strings) in descending order
    """
    dates = session.query(FundPerformance.report_date).distinct().order_by(
        desc(FundPerformance.report_date)
    ).all()

    return [d[0].isoformat() for d in dates]


def get_performance_ranking(
    session: Session,
    metric: str = 'annual_return',
    report_date: Optional[date] = None,
    strategy_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    limit: int = 50
) -> List[Dict[str, Any]]:
    """Get fund performance ranking by specified metric

    Args:
        session: Database session
        metric: Performance metric to rank by (default: annual_return)
        report_date: Report date filter (default: latest date)
        strategy_id: Strategy ID filter
        manager_id: Manager ID filter
        limit: Maximum number of results (1-200)

    Returns:
        List of fund performance records with ranking
    """
    # Validate metric
    if metric not in VALID_PERFORMANCE_FIELDS:
        logger.warning(f"Invalid metric: {metric}, using annual_return")
        metric = 'annual_return'

    # Limit validation
    limit = max(1, min(limit, 200))

    # Get latest report date if not specified
    if not report_date:
        report_date = session.query(func.max(FundPerformance.report_date)).scalar()

    if not report_date:
        return []

    # Build query
    query = session.query(
        FundPerformance,
        Fund,
        Manager.manager_name,
        Strategy.level3_category.label('strategy_name')
    ).join(
        Fund, FundPerformance.fund_code == Fund.fund_code
    ).outerjoin(
        Manager, Fund.manager_id == Manager.manager_id
    ).outerjoin(
        Strategy, Fund.strategy_id == Strategy.strategy_id
    ).filter(
        FundPerformance.report_date == report_date
    )

    # Apply filters
    if strategy_id:
        query = query.filter(Fund.strategy_id == strategy_id)
    if manager_id:
        query = query.filter(Fund.manager_id == manager_id)

    # Order by metric (descending for returns, ascending for drawdowns)
    metric_attr = getattr(FundPerformance, metric)
    if 'drawdown' in metric.lower():
        query = query.filter(metric_attr.isnot(None)).order_by(asc(metric_attr))
    else:
        query = query.filter(metric_attr.isnot(None)).order_by(desc(metric_attr))

    # Limit results
    query = query.limit(limit)

    # Execute and format results
    results = []
    for rank, (perf, fund, manager_name, strategy_name) in enumerate(query.all(), 1):
        value = getattr(perf, metric)
        results.append({
            'rank': rank,
            'fund_code': fund.fund_code,
            'fund_name': fund.fund_name,
            'manager_name': manager_name,
            'strategy_name': strategy_name,
            'value': float(value) if value else None,
            'report_date': perf.report_date.isoformat()
        })

    return results


def get_strategy_distribution(session: Session, report_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Get fund count distribution by strategy

    Args:
        session: Database session
        report_date: Report date filter (default: latest date)

    Returns:
        List of strategy distribution records
    """
    # Get latest report date if not specified
    if not report_date:
        report_date = session.query(func.max(FundPerformance.report_date)).scalar()

    if not report_date:
        return []

    # Query
    query = session.query(
        Strategy.level1_category,
        Strategy.level2_category,
        Strategy.level3_category,
        func.count(func.distinct(FundPerformance.fund_code)).label('fund_count')
    ).outerjoin(
        Fund, Strategy.strategy_id == Fund.strategy_id
    ).outerjoin(
        FundPerformance,
        and_(
            Fund.fund_code == FundPerformance.fund_code,
            FundPerformance.report_date == report_date
        )
    ).group_by(
        Strategy.strategy_id
    ).order_by(
        desc('fund_count')
    )

    results = []
    for level1, level2, level3, count in query.all():
        results.append({
            'level1_category': level1,
            'level2_category': level2,
            'level3_category': level3,
            'fund_count': count
        })

    return results


# ===== Fund Queries =====

def search_funds(
    session: Session,
    keyword: Optional[str] = None,
    strategy_id: Optional[int] = None,
    manager_id: Optional[int] = None,
    report_date: Optional[date] = None,
    sort_by: str = 'annual_return',
    sort_order: str = 'desc',
    offset: int = 0,
    limit: int = 20
) -> Dict[str, Any]:
    """Search funds with filters and pagination

    Args:
        session: Database session
        keyword: Search keyword (fund name or manager name)
        strategy_id: Strategy ID filter
        manager_id: Manager ID filter
        report_date: Report date filter (default: latest date)
        sort_by: Sort field (default: annual_return)
        sort_order: Sort order ('asc' or 'desc', default: 'desc')
        offset: Pagination offset
        limit: Pagination limit (1-100)

    Returns:
        Dictionary with 'items' and 'total' keys
    """
    # Validate inputs
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    if sort_by not in VALID_PERFORMANCE_FIELDS:
        sort_by = 'annual_return'

    # Get latest report date if not specified
    if not report_date:
        report_date = session.query(func.max(FundPerformance.report_date)).scalar()

    if not report_date:
        return {'items': [], 'total': 0}

    # Build base query
    query = session.query(
        Fund,
        FundPerformance,
        Manager.manager_name,
        Strategy.level1_category,
        Strategy.level2_category,
        Strategy.level3_category
    ).join(
        FundPerformance, Fund.fund_code == FundPerformance.fund_code
    ).outerjoin(
        Manager, Fund.manager_id == Manager.manager_id
    ).outerjoin(
        Strategy, Fund.strategy_id == Strategy.strategy_id
    ).filter(
        FundPerformance.report_date == report_date
    )

    # Apply filters
    if keyword:
        query = query.filter(
            or_(
                Fund.fund_name.contains(keyword),
                Manager.manager_name.contains(keyword)
            )
        )

    if strategy_id:
        query = query.filter(Fund.strategy_id == strategy_id)

    if manager_id:
        query = query.filter(Fund.manager_id == manager_id)

    # Get total count
    total = query.count()

    # Apply sorting
    sort_attr = getattr(FundPerformance, sort_by)
    if sort_order.lower() == 'asc':
        query = query.order_by(asc(sort_attr))
    else:
        query = query.order_by(desc(sort_attr))

    # Apply pagination
    query = query.offset(offset).limit(limit)

    # Execute and format results
    items = []
    for fund, perf, manager_name, level1, level2, level3 in query.all():
        # Build performance snapshot
        latest_performance = {
            'report_date': perf.report_date.isoformat(),
        }

        # Add all performance fields to latest_performance
        for field in VALID_PERFORMANCE_FIELDS:
            value = getattr(perf, field)
            latest_performance[field] = float(value) if value else None

        item = {
            'fund_code': fund.fund_code,
            'fund_name': fund.fund_name,
            'manager_name': manager_name,
            'strategy_name': level3,  # Frontend expects strategy_name
            'strategy_level1': level1,
            'strategy_level2': level2,
            'strategy_level3': level3,
            'launch_date': fund.launch_date.isoformat() if fund.launch_date else None,
            'latest_performance': latest_performance,  # Nest performance data here
        }

        items.append(item)

    return {'items': items, 'total': total}


def get_fund_detail(session: Session, fund_code: str, report_date: Optional[date] = None) -> Optional[Dict[str, Any]]:
    """Get detailed information for a specific fund

    Args:
        session: Database session
        fund_code: Fund code
        report_date: Report date filter (default: latest date)

    Returns:
        Fund detail dictionary or None if not found
    """
    # Get latest report date if not specified
    if not report_date:
        report_date = session.query(func.max(FundPerformance.report_date)).scalar()

    if not report_date:
        return None

    # Query
    result = session.query(
        Fund,
        FundPerformance,
        Manager,
        Strategy
    ).outerjoin(
        FundPerformance,
        and_(
            Fund.fund_code == FundPerformance.fund_code,
            FundPerformance.report_date == report_date
        )
    ).outerjoin(
        Manager, Fund.manager_id == Manager.manager_id
    ).outerjoin(
        Strategy, Fund.strategy_id == Strategy.strategy_id
    ).filter(
        Fund.fund_code == fund_code
    ).first()

    if not result:
        return None

    fund, perf, manager, strategy = result

    detail = {
        'fund_code': fund.fund_code,
        'fund_name': fund.fund_name,
        'launch_date': fund.launch_date.isoformat() if fund.launch_date else None,
        'manager': {
            'manager_id': manager.manager_id if manager else None,
            'manager_name': manager.manager_name if manager else None,
            'establishment_date': manager.establishment_date.isoformat() if manager and manager.establishment_date else None,
            'company_size': manager.company_size if manager else None
        } if manager else None,
        'strategy': {
            'strategy_id': strategy.strategy_id if strategy else None,
            'level1_category': strategy.level1_category if strategy else None,
            'level2_category': strategy.level2_category if strategy else None,
            'level3_category': strategy.level3_category if strategy else None
        } if strategy else None,
        'performance': {}
    }

    # Add performance fields
    if perf:
        detail['performance']['report_date'] = perf.report_date.isoformat()
        for field in VALID_PERFORMANCE_FIELDS:
            value = getattr(perf, field)
            detail['performance'][field] = float(value) if value else None

    return detail


# ===== Strategy Queries =====

def get_all_strategies(session: Session, report_date: Optional[date] = None) -> List[Dict[str, Any]]:
    """Get all strategies with fund counts

    Args:
        session: Database session
        report_date: Optional report date for counting funds (default: latest date)

    Returns:
        List of strategy records with fund counts
    """
    # Get latest report date if not specified
    if not report_date:
        report_date = session.query(func.max(FundPerformance.report_date)).scalar()

    # Query strategies with fund counts
    query = session.query(
        Strategy,
        func.count(func.distinct(FundPerformance.fund_code)).label('fund_count')
    ).outerjoin(
        Fund, Strategy.strategy_id == Fund.strategy_id
    )

    if report_date:
        query = query.outerjoin(
            FundPerformance,
            and_(
                Fund.fund_code == FundPerformance.fund_code,
                FundPerformance.report_date == report_date
            )
        )

    query = query.group_by(Strategy.strategy_id).order_by(
        Strategy.level1_category,
        Strategy.level2_category,
        Strategy.level3_category
    )

    results = []
    for s, fund_count in query.all():
        results.append({
            'strategy_id': s.strategy_id,
            'strategy_name': s.level3_category,  # Frontend expects strategy_name
            'level1_category': s.level1_category,
            'level2_category': s.level2_category,
            'level3_category': s.level3_category,
            'fund_count': fund_count
        })

    return results


# ===== Manager Queries =====

def get_all_managers(session: Session, limit: int = 1000) -> List[Dict[str, Any]]:
    """Get all managers

    Args:
        session: Database session
        limit: Maximum number of results

    Returns:
        List of manager records
    """
    managers = session.query(Manager).order_by(
        Manager.manager_name
    ).limit(limit).all()

    results = []
    for m in managers:
        results.append({
            'manager_id': m.manager_id,
            'manager_name': m.manager_name,
            'establishment_date': m.establishment_date.isoformat() if m.establishment_date else None,
            'company_size': m.company_size
        })

    return results
