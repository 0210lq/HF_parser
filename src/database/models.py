"""
Database models for HF Parser
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, DECIMAL, BigInteger, Text, Index
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all models"""
    pass


# Strategy Hierarchy - Three-level classification system
STRATEGY_HIERARCHY = {
    '指增300': ('股票策略', '指数增强'),
    '指增500': ('股票策略', '指数增强'),
    '指增1000': ('股票策略', '指数增强'),
    '其他指增': ('股票策略', '指数增强'),
    '量化选股': ('股票策略', '量化选股'),
    '主观股票': ('股票策略', '主观股票'),
    '中性策略': ('股票策略', '中性策略'),
    '量化商品': ('商品策略', '量化CTA'),
    '主观商品': ('商品策略', '主观CTA'),
    '量化商品套利': ('套利策略', '商品套利'),
    '主观商品套利': ('套利策略', '商品套利'),
    '期权套利': ('套利策略', '期权套利'),
    'ETF套利': ('套利策略', 'ETF套利'),
    '股指套利': ('套利策略', '股指套利'),
    '多策略套利': ('套利策略', '多策略套利'),
    '固收': ('固收策略', '纯债'),
    '固收+': ('固收策略', '固收增强'),
    '债券复合': ('固收策略', '债券复合'),
    '转债策略': ('固收策略', '转债'),
    '宏观策略': ('宏观策略', '宏观策略'),
    '多策略': ('多策略', '多策略'),
    'FOF': ('多策略', 'FOF'),
    '未分类': ('未分类', '未分类'),
}


# Valid performance field names
VALID_PERFORMANCE_FIELDS = {
    'weekly_excess', 'weekly_return',
    'monthly_excess', 'monthly_return', 'monthly_max_drawdown',
    'quarterly_excess', 'quarterly_return', 'quarterly_max_drawdown',
    'semi_annual_excess', 'semi_annual_return', 'semi_annual_max_drawdown',
    'annual_excess', 'annual_return_ytd', 'annual_max_drawdown',
    'ytd_excess', 'ytd_return', 'ytd_max_drawdown',
    'annual_return', 'cumulative_return', 'max_drawdown', 'annual_volatility',
    'annual_sharpe', 'annual_calmar', 'annual_sortino',
    'inception_sharpe', 'inception_calmar', 'inception_sortino'
}


class Manager(Base):
    """Manager (Asset Management Company) Model"""
    __tablename__ = 'managers'
    __table_args__ = {'comment': '管理人维度表'}

    manager_id = Column(Integer, primary_key=True, autoincrement=True, comment='管理人ID')
    manager_name = Column(String(200), nullable=False, unique=True, comment='管理人名称')
    establishment_date = Column(Date, nullable=True, comment='公司成立日期')
    company_size = Column(String(50), nullable=True, comment='公司规模')
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # Relationships
    funds = relationship("Fund", back_populates="manager")

    def __repr__(self):
        return f"<Manager(id={self.manager_id}, name={self.manager_name})>"


class Strategy(Base):
    """Strategy Classification Model - Three-level hierarchy"""
    __tablename__ = 'strategies'
    __table_args__ = (
        Index('idx_level1', 'level1_category'),
        Index('idx_level2', 'level2_category'),
        {'comment': '策略分类维度表'}
    )

    strategy_id = Column(Integer, primary_key=True, autoincrement=True, comment='策略ID')
    level3_category = Column(String(100), nullable=False, unique=True, comment='三级分类（Sheet名）')
    level2_category = Column(String(100), nullable=False, comment='二级分类')
    level1_category = Column(String(100), nullable=False, comment='一级分类')
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # Relationships
    funds = relationship("Fund", back_populates="strategy")

    def __repr__(self):
        return f"<Strategy(id={self.strategy_id}, L1={self.level1_category}, L2={self.level2_category}, L3={self.level3_category})>"


class Fund(Base):
    """Fund Product Model"""
    __tablename__ = 'funds'
    __table_args__ = (
        Index('idx_fund_name', 'fund_name'),
        Index('idx_manager', 'manager_id'),
        Index('idx_strategy', 'strategy_id'),
        {'comment': '产品主表'}
    )

    fund_code = Column(String(50), primary_key=True, comment='产品代码')
    fund_name = Column(String(300), nullable=False, comment='产品名称')
    manager_id = Column(Integer, ForeignKey('managers.manager_id', ondelete='SET NULL'), nullable=True, comment='管理人ID')
    strategy_id = Column(Integer, ForeignKey('strategies.strategy_id', ondelete='SET NULL'), nullable=True, comment='策略ID')
    launch_date = Column(Date, nullable=True, comment='成立日期')
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment='更新时间')

    # Relationships
    manager = relationship("Manager", back_populates="funds")
    strategy = relationship("Strategy", back_populates="funds")
    performances = relationship("FundPerformance", back_populates="fund", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Fund(code={self.fund_code}, name={self.fund_name})>"


class FundPerformance(Base):
    """Fund Performance Time Series Model"""
    __tablename__ = 'fund_performance'
    __table_args__ = (
        Index('uk_fund_date', 'fund_code', 'report_date', unique=True),
        Index('idx_report_date', 'report_date'),
        Index('idx_annual_return', 'annual_return'),
        Index('idx_cumulative_return', 'cumulative_return'),
        {'comment': '业绩时间序列表'}
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='记录ID')
    fund_code = Column(String(50), ForeignKey('funds.fund_code', ondelete='CASCADE'), nullable=False, comment='产品代码')
    report_date = Column(Date, nullable=False, comment='报告日期')
    data_source = Column(String(20), nullable=False, default='excel', comment='数据来源')

    # Weekly performance
    weekly_excess = Column(DECIMAL(10, 6), nullable=True, comment='近一周超额')
    weekly_return = Column(DECIMAL(10, 6), nullable=True, comment='近一周收益率')

    # Monthly performance
    monthly_excess = Column(DECIMAL(10, 6), nullable=True, comment='近一月超额')
    monthly_return = Column(DECIMAL(10, 6), nullable=True, comment='近一月收益率')
    monthly_max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='近一月最大回撤')

    # Quarterly performance
    quarterly_excess = Column(DECIMAL(10, 6), nullable=True, comment='近三月超额')
    quarterly_return = Column(DECIMAL(10, 6), nullable=True, comment='近三月收益率')
    quarterly_max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='近三月最大回撤')

    # Semi-annual performance (annualized)
    semi_annual_excess = Column(DECIMAL(10, 6), nullable=True, comment='近六月超额(年化)')
    semi_annual_return = Column(DECIMAL(10, 6), nullable=True, comment='近六月收益率(年化)')
    semi_annual_max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='近六月最大回撤')

    # Annual performance (annualized)
    annual_excess = Column(DECIMAL(10, 6), nullable=True, comment='近一年超额(年化)')
    annual_return_ytd = Column(DECIMAL(10, 6), nullable=True, comment='近一年收益率(年化)')
    annual_max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='近一年最大回撤')

    # Year-to-date performance
    ytd_excess = Column(DECIMAL(10, 6), nullable=True, comment='今年以来超额')
    ytd_return = Column(DECIMAL(10, 6), nullable=True, comment='今年以来收益率')
    ytd_max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='今年以来最大回撤')

    # Since inception performance
    annual_return = Column(DECIMAL(10, 6), nullable=True, comment='成立以来年化收益率')
    cumulative_return = Column(DECIMAL(12, 6), nullable=True, comment='成立以来累计收益')
    max_drawdown = Column(DECIMAL(10, 6), nullable=True, comment='成立以来最大回撤')
    annual_volatility = Column(DECIMAL(10, 6), nullable=True, comment='成立以来年化波动率')

    # Risk-adjusted metrics - Annual
    annual_sharpe = Column(DECIMAL(8, 4), nullable=True, comment='近一年夏普比率')
    annual_calmar = Column(DECIMAL(8, 4), nullable=True, comment='近一年卡玛比率')
    annual_sortino = Column(DECIMAL(8, 4), nullable=True, comment='近一年索提诺比率')

    # Risk-adjusted metrics - Since inception
    inception_sharpe = Column(DECIMAL(8, 4), nullable=True, comment='成立以来夏普比率')
    inception_calmar = Column(DECIMAL(8, 4), nullable=True, comment='成立以来卡玛比率')
    inception_sortino = Column(DECIMAL(8, 4), nullable=True, comment='成立以来索提诺比率')

    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')

    # Relationships
    fund = relationship("Fund", back_populates="performances")

    def __repr__(self):
        return f"<FundPerformance(fund_code={self.fund_code}, report_date={self.report_date})>"


class ReportMetadata(Base):
    """Report Metadata Model"""
    __tablename__ = 'report_metadata'
    __table_args__ = {'comment': '报告元数据表'}

    report_id = Column(Integer, primary_key=True, autoincrement=True, comment='报告ID')
    report_date = Column(Date, nullable=False, unique=True, comment='报告日期')
    pdf_filename = Column(String(300), nullable=True, comment='PDF文件名')
    excel_filename = Column(String(300), nullable=True, comment='Excel文件名')
    total_funds = Column(Integer, nullable=True, comment='基金总数')
    total_strategies = Column(Integer, nullable=True, comment='策略总数')
    parse_status = Column(String(20), nullable=False, default='pending', comment='解析状态')
    error_log = Column(Text, nullable=True, comment='错误日志')
    created_at = Column(DateTime, nullable=False, server_default=func.now(), comment='创建时间')

    def __repr__(self):
        return f"<ReportMetadata(date={self.report_date}, status={self.parse_status})>"
