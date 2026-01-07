"""
Import 1219 Weekly Report Data

This script imports data from the 2025-12-19 weekly report:
1. Uses 1205 Excel to get product code mappings (by product name)
2. Imports 1219 Excel data with strategy classification based on sheet names
3. Creates managers, strategies, funds, and performance records
"""
import os
import sys
import hashlib
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

import pandas as pd
from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from dotenv import load_dotenv

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(Path(__file__).parent))

from src.database.models import (
    Base, Manager, Strategy, Fund, FundPerformance, ReportMetadata,
    STRATEGY_HIERARCHY, VALID_PERFORMANCE_FIELDS
)

# Load environment
load_dotenv()

# Database connection
DB_URL = f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DATABASE')}?charset=utf8mb4"

# Data paths
DATA_DIR = Path(__file__).parent / "data"
EXCEL_DIR = DATA_DIR / "excel"


def percent_to_decimal(value) -> Optional[Decimal]:
    """Convert percentage string to decimal"""
    if pd.isna(value):
        return None

    if isinstance(value, (int, float)):
        # Check for NaN
        import math
        if math.isnan(value):
            return None
        # If already a number, assume it's a percentage (e.g., 5.23 means 5.23%)
        if abs(value) > 10:  # Likely already a percentage
            return Decimal(str(value / 100)).quantize(Decimal('0.000001'))
        return Decimal(str(value)).quantize(Decimal('0.000001'))

    s = str(value).strip()
    if not s or s.lower() in ('nan', 'none', '-', '', 'nan%'):
        return None

    # Remove percentage sign
    s = s.replace('%', '').strip()

    try:
        val = float(s)
        import math
        if math.isnan(val):
            return None
        return Decimal(str(val / 100)).quantize(Decimal('0.000001'))
    except (ValueError, InvalidOperation):
        return None


def parse_date_value(value) -> Optional[date]:
    """Parse date from various formats"""
    if pd.isna(value):
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, pd.Timestamp):
        return value.date()

    s = str(value).strip()
    if not s or s.lower() in ('nan', 'none', ''):
        return None

    # Try common formats
    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y.%m.%d']:
        try:
            return datetime.strptime(s[:10], fmt).date()
        except ValueError:
            continue

    return None


def generate_temp_code(fund_name: str, manager_name: str) -> str:
    """Generate a temporary product code for unmatched products"""
    key = f"{fund_name}_{manager_name}"
    hash_val = hashlib.md5(key.encode()).hexdigest()[:8].upper()
    return f"TMP_{hash_val}"


def build_name_to_code_mapping() -> Dict[str, str]:
    """Build product name -> product code mapping from 1205 Excel"""
    xlsx_path = EXCEL_DIR / "私募周报1205.xlsx"
    if not xlsx_path.exists():
        logger.warning(f"1205 Excel not found: {xlsx_path}")
        return {}

    xlsx = pd.ExcelFile(xlsx_path)
    name_to_code = {}

    for sheet in xlsx.sheet_names:
        if sheet == '策略汇总':
            continue

        df = pd.read_excel(xlsx, sheet_name=sheet)

        code_col = name_col = None
        for col in df.columns:
            col_str = str(col).strip()
            if '产品代码' in col_str:
                code_col = col
            elif '产品简称' in col_str:
                name_col = col

        if not all([code_col, name_col]):
            continue

        for _, row in df.iterrows():
            code = str(row.get(code_col, '')).strip()
            name = str(row.get(name_col, '')).strip()
            if code and code != 'nan' and name and name != 'nan':
                name_to_code[name] = code

    logger.info(f"Built name->code mapping: {len(name_to_code)} entries")
    return name_to_code


def parse_1219_excel(name_to_code: Dict[str, str]) -> Tuple[List[Dict], Dict[str, int]]:
    """Parse 1219 Excel and return records with statistics"""
    xlsx_path = EXCEL_DIR / "私募周报1219.xlsx"
    if not xlsx_path.exists():
        logger.error(f"1219 Excel not found: {xlsx_path}")
        return [], {}

    xlsx = pd.ExcelFile(xlsx_path)
    all_records = []
    stats = {'matched': 0, 'generated': 0, 'by_strategy': {}}

    # Column mapping - supports both "超额" (excess) and "收益率" (return) formats
    COLUMN_MAP = {
        '机构简称': 'manager_name',
        '公司成立时间': 'establishment_date',
        '公司规模': 'company_size',
        '产品简称': 'fund_name',
        '成立日期': 'launch_date',
        # Weekly
        '近一周超额': 'weekly_excess',
        '近一周收益率': 'weekly_return',
        # Monthly
        '近一月超额': 'monthly_excess',
        '近一月收益率': 'monthly_return',
        '近一月超额最大回撤': 'monthly_max_drawdown',
        '近一月最大回撤': 'monthly_max_drawdown',
        # Quarterly
        '近三月超额': 'quarterly_excess',
        '近三月收益率': 'quarterly_return',
        '近三月超额最大回撤': 'quarterly_max_drawdown',
        '近三月最大回撤': 'quarterly_max_drawdown',
        # Semi-annual
        '近六月超额(年化)': 'semi_annual_excess',
        '近六月收益率(年化)': 'semi_annual_return',
        '近六月超额最大回撤': 'semi_annual_max_drawdown',
        '近六月最大回撤': 'semi_annual_max_drawdown',
        # Annual
        '近一年超额(年化)': 'annual_excess',
        '近一年收益率(年化)': 'annual_return_ytd',
        '近一年超额最大回撤': 'annual_max_drawdown',
        '近一年最大回撤': 'annual_max_drawdown',
        # YTD
        '今年以来超额': 'ytd_excess',
        '今年以来收益率': 'ytd_return',
        '今年以来超额最大回撤': 'ytd_max_drawdown',
        '今年以来最大回撤': 'ytd_max_drawdown',
        # Since inception
        '成立以来超额年化收益率': 'annual_return',
        '成立以来年化收益率': 'annual_return',
        '成立以来累计超额': 'cumulative_return',
        '成立以来累计收益': 'cumulative_return',
        '成立以来超额最大回撤': 'max_drawdown',
        '成立以来最大回撤': 'max_drawdown',
        '成立以来超额年化波动率': 'annual_volatility',
        '成立以来年化波动率': 'annual_volatility',
        # Risk metrics - annual
        '近一年超额夏普比率': 'annual_sharpe',
        '近一年夏普比率': 'annual_sharpe',
        '近一年超额卡玛比率': 'annual_calmar',
        '近一年卡玛比率': 'annual_calmar',
        '近一年超额索提诺比率': 'annual_sortino',
        '近一年索提诺比率': 'annual_sortino',
        # Risk metrics - inception
        '成立以来超额夏普比率': 'inception_sharpe',
        '成立以来夏普比率': 'inception_sharpe',
        '成立以来超额卡玛比率': 'inception_calmar',
        '成立以来卡玛比率': 'inception_calmar',
        '成立以来超额索提诺比率': 'inception_sortino',
        '成立以来索提诺比率': 'inception_sortino',
    }

    PERCENT_FIELDS = {
        'weekly_excess', 'weekly_return',
        'monthly_excess', 'monthly_return', 'monthly_max_drawdown',
        'quarterly_excess', 'quarterly_return', 'quarterly_max_drawdown',
        'semi_annual_excess', 'semi_annual_return', 'semi_annual_max_drawdown',
        'annual_excess', 'annual_return_ytd', 'annual_max_drawdown',
        'ytd_excess', 'ytd_return', 'ytd_max_drawdown',
        'annual_return', 'cumulative_return', 'max_drawdown', 'annual_volatility'
    }

    for sheet_name in xlsx.sheet_names:
        if sheet_name == '策略汇总':
            continue

        # Sheet name is the level3 strategy
        level3_strategy = sheet_name
        if level3_strategy not in STRATEGY_HIERARCHY:
            logger.warning(f"Unknown strategy: {level3_strategy}, will use '未分类'")
            level3_strategy = '未分类'

        df = pd.read_excel(xlsx, sheet_name=sheet_name)
        sheet_count = 0

        for _, row in df.iterrows():
            record = {'level3_strategy': level3_strategy}

            # Map columns
            for cn_col, en_col in COLUMN_MAP.items():
                for df_col in df.columns:
                    if cn_col in str(df_col):
                        value = row.get(df_col)

                        # Convert based on field type
                        if en_col in PERCENT_FIELDS:
                            record[en_col] = percent_to_decimal(value)
                        elif en_col in ('establishment_date', 'launch_date'):
                            record[en_col] = parse_date_value(value)
                        elif en_col in ('annual_sharpe', 'annual_calmar', 'annual_sortino',
                                       'inception_sharpe', 'inception_calmar', 'inception_sortino'):
                            # Ratio fields - no percentage conversion
                            if pd.notna(value):
                                try:
                                    import math
                                    float_val = float(value)
                                    if math.isnan(float_val):
                                        record[en_col] = None
                                    else:
                                        record[en_col] = Decimal(str(float_val)).quantize(Decimal('0.0001'))
                                except (ValueError, InvalidOperation, TypeError):
                                    record[en_col] = None
                            else:
                                record[en_col] = None
                        else:
                            record[en_col] = str(value).strip() if pd.notna(value) else None
                        break

            # Get or generate product code
            fund_name = record.get('fund_name')
            manager_name = record.get('manager_name')

            if not fund_name:
                continue

            if fund_name in name_to_code:
                record['fund_code'] = name_to_code[fund_name]
                stats['matched'] += 1
            else:
                record['fund_code'] = generate_temp_code(fund_name, manager_name or '')
                stats['generated'] += 1

            all_records.append(record)
            sheet_count += 1

        stats['by_strategy'][sheet_name] = sheet_count
        logger.debug(f"Parsed sheet '{sheet_name}': {sheet_count} records")

    logger.info(f"Parsed 1219 Excel: {len(all_records)} total records")
    logger.info(f"  Matched: {stats['matched']}, Generated codes: {stats['generated']}")

    return all_records, stats


def import_to_database(records: List[Dict], report_date: date) -> Dict[str, int]:
    """Import records to database"""
    engine = create_engine(DB_URL, echo=False)

    # Create tables
    Base.metadata.create_all(engine)

    stats = {
        'managers': 0,
        'strategies': 0,
        'funds': 0,
        'performances': 0,
        'updated_funds': 0,
        'skipped': 0
    }

    with Session(engine) as session:
        try:
            # 1. Insert strategies
            logger.info("Inserting strategies...")
            strategy_cache = {}
            for level3, (level1, level2) in STRATEGY_HIERARCHY.items():
                existing = session.query(Strategy).filter_by(level3_category=level3).first()
                if not existing:
                    strategy = Strategy(
                        level3_category=level3,
                        level2_category=level2,
                        level1_category=level1
                    )
                    session.add(strategy)
                    session.flush()
                    strategy_cache[level3] = strategy.strategy_id
                    stats['strategies'] += 1
                else:
                    strategy_cache[level3] = existing.strategy_id

            session.commit()
            logger.info(f"Strategies: {stats['strategies']} new")

            # 2. Insert managers
            logger.info("Inserting managers...")
            manager_cache = {}
            unique_managers = set()
            for r in records:
                if r.get('manager_name'):
                    unique_managers.add((
                        r['manager_name'],
                        r.get('establishment_date'),
                        r.get('company_size')
                    ))

            for manager_name, est_date, size in unique_managers:
                existing = session.query(Manager).filter_by(manager_name=manager_name).first()
                if not existing:
                    manager = Manager(
                        manager_name=manager_name,
                        establishment_date=est_date,
                        company_size=size
                    )
                    session.add(manager)
                    session.flush()
                    manager_cache[manager_name] = manager.manager_id
                    stats['managers'] += 1
                else:
                    manager_cache[manager_name] = existing.manager_id

            session.commit()
            logger.info(f"Managers: {stats['managers']} new")

            # 3. Insert/update funds and performance
            logger.info("Inserting funds and performance...")
            for r in records:
                fund_code = r.get('fund_code')
                fund_name = r.get('fund_name')

                if not fund_code or not fund_name:
                    stats['skipped'] += 1
                    continue

                # Get strategy_id
                level3 = r.get('level3_strategy', '未分类')
                strategy_id = strategy_cache.get(level3)

                # Get manager_id
                manager_name = r.get('manager_name')
                manager_id = manager_cache.get(manager_name) if manager_name else None

                # Insert/update fund
                existing_fund = session.query(Fund).filter_by(fund_code=fund_code).first()
                if not existing_fund:
                    fund = Fund(
                        fund_code=fund_code,
                        fund_name=fund_name,
                        manager_id=manager_id,
                        strategy_id=strategy_id,
                        launch_date=r.get('launch_date')
                    )
                    session.add(fund)
                    stats['funds'] += 1
                else:
                    # Update existing fund if needed
                    if strategy_id and not existing_fund.strategy_id:
                        existing_fund.strategy_id = strategy_id
                        stats['updated_funds'] += 1

                # Insert performance
                existing_perf = session.query(FundPerformance).filter_by(
                    fund_code=fund_code,
                    report_date=report_date
                ).first()

                if not existing_perf:
                    perf = FundPerformance(
                        fund_code=fund_code,
                        report_date=report_date,
                        data_source='excel',
                        # Weekly
                        weekly_excess=r.get('weekly_excess'),
                        weekly_return=r.get('weekly_return'),
                        # Monthly
                        monthly_excess=r.get('monthly_excess'),
                        monthly_return=r.get('monthly_return'),
                        monthly_max_drawdown=r.get('monthly_max_drawdown'),
                        # Quarterly
                        quarterly_excess=r.get('quarterly_excess'),
                        quarterly_return=r.get('quarterly_return'),
                        quarterly_max_drawdown=r.get('quarterly_max_drawdown'),
                        # Semi-annual
                        semi_annual_excess=r.get('semi_annual_excess'),
                        semi_annual_return=r.get('semi_annual_return'),
                        semi_annual_max_drawdown=r.get('semi_annual_max_drawdown'),
                        # Annual
                        annual_excess=r.get('annual_excess'),
                        annual_return_ytd=r.get('annual_return_ytd'),
                        annual_max_drawdown=r.get('annual_max_drawdown'),
                        # YTD
                        ytd_excess=r.get('ytd_excess'),
                        ytd_return=r.get('ytd_return'),
                        ytd_max_drawdown=r.get('ytd_max_drawdown'),
                        # Since inception
                        annual_return=r.get('annual_return'),
                        cumulative_return=r.get('cumulative_return'),
                        max_drawdown=r.get('max_drawdown'),
                        annual_volatility=r.get('annual_volatility'),
                        # Risk metrics
                        annual_sharpe=r.get('annual_sharpe'),
                        annual_calmar=r.get('annual_calmar'),
                        annual_sortino=r.get('annual_sortino'),
                        inception_sharpe=r.get('inception_sharpe'),
                        inception_calmar=r.get('inception_calmar'),
                        inception_sortino=r.get('inception_sortino'),
                    )
                    session.add(perf)
                    stats['performances'] += 1

            session.commit()

            # 4. Insert report metadata
            existing_meta = session.query(ReportMetadata).filter_by(report_date=report_date).first()
            if not existing_meta:
                meta = ReportMetadata(
                    report_date=report_date,
                    excel_filename='私募周报1219.xlsx',
                    total_funds=stats['funds'] + stats['updated_funds'],
                    total_strategies=len(STRATEGY_HIERARCHY),
                    parse_status='completed'
                )
                session.add(meta)
                session.commit()

            logger.info(f"Import completed:")
            logger.info(f"  Strategies: {stats['strategies']}")
            logger.info(f"  Managers: {stats['managers']}")
            logger.info(f"  Funds: {stats['funds']} new, {stats['updated_funds']} updated")
            logger.info(f"  Performances: {stats['performances']}")
            logger.info(f"  Skipped: {stats['skipped']}")

        except Exception as e:
            session.rollback()
            logger.error(f"Import failed: {e}")
            raise

    return stats


def main():
    """Main entry point"""
    logger.info("=" * 60)
    logger.info("Starting 1219 Weekly Report Import")
    logger.info("=" * 60)

    # Build mapping from 1205
    name_to_code = build_name_to_code_mapping()

    # Parse 1219 Excel
    records, parse_stats = parse_1219_excel(name_to_code)

    if not records:
        logger.error("No records parsed, aborting import")
        return

    # Import to database
    report_date = date(2025, 12, 19)
    import_stats = import_to_database(records, report_date)

    # Summary
    logger.info("=" * 60)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Report Date: {report_date}")
    logger.info(f"Total Records: {len(records)}")
    logger.info(f"Code Matched: {parse_stats['matched']}")
    logger.info(f"Code Generated: {parse_stats['generated']}")
    logger.info("")
    logger.info("By Strategy:")
    for strategy, count in parse_stats['by_strategy'].items():
        logger.info(f"  {strategy}: {count}")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
