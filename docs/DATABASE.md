# 数据库设计文档

## 概述

HF Parser 使用 MySQL 8.0 作为数据存储，采用 SQLAlchemy 2.0 ORM 进行数据库操作。数据库设计遵循第三范式，支持私募基金周报数据的存储和查询。

## 数据库配置

```sql
-- 创建数据库
CREATE DATABASE hf_tracker CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE hf_tracker;
```

## ER 图

```
┌─────────────┐       ┌─────────────┐       ┌─────────────────┐
│  managers   │       │  strategies │       │ report_metadata │
├─────────────┤       ├─────────────┤       ├─────────────────┤
│ manager_id  │       │ strategy_id │       │ report_id       │
│ manager_name│       │ level3_cat  │       │ report_date     │
│ est_date    │       │ level2_cat  │       │ pdf_filename    │
│ company_size│       │ level1_cat  │       │ excel_filename  │
└──────┬──────┘       └──────┬──────┘       │ total_funds     │
       │                     │              │ parse_status    │
       │ 1:N                 │ 1:N          └─────────────────┘
       │                     │
       ▼                     ▼
┌──────────────────────────────────┐
│              funds               │
├──────────────────────────────────┤
│ fund_code (PK)                   │
│ fund_name                        │
│ manager_id (FK) ─────────────────┼──► managers
│ strategy_id (FK) ────────────────┼──► strategies
│ launch_date                      │
└────────────────┬─────────────────┘
                 │
                 │ 1:N
                 ▼
┌──────────────────────────────────┐
│        fund_performance          │
├──────────────────────────────────┤
│ id (PK)                          │
│ fund_code (FK) ──────────────────┼──► funds
│ report_date                      │
│ weekly_return, weekly_excess     │
│ monthly_return, monthly_excess   │
│ ... (27个业绩指标字段)           │
└──────────────────────────────────┘
```

## 表结构详解

### 1. managers - 管理人表

存储私募基金管理人（公司）信息。

```sql
CREATE TABLE managers (
    manager_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '管理人ID',
    manager_name VARCHAR(200) NOT NULL UNIQUE COMMENT '管理人名称',
    establishment_date DATE COMMENT '公司成立日期',
    company_size VARCHAR(50) COMMENT '公司规模',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='管理人维度表';
```

| 字段 | 类型 | 说明 |
|------|------|------|
| manager_id | INT | 主键，自增 |
| manager_name | VARCHAR(200) | 管理人名称，唯一 |
| establishment_date | DATE | 公司成立日期 |
| company_size | VARCHAR(50) | 公司规模（如"50-100亿"） |
| created_at | DATETIME | 记录创建时间 |
| updated_at | DATETIME | 记录更新时间 |

### 2. strategies - 策略分类表

存储三级策略分类体系。

```sql
CREATE TABLE strategies (
    strategy_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '策略ID',
    level3_category VARCHAR(100) NOT NULL UNIQUE COMMENT '三级分类（Sheet名）',
    level2_category VARCHAR(100) NOT NULL COMMENT '二级分类',
    level1_category VARCHAR(100) NOT NULL COMMENT '一级分类',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_level1 (level1_category),
    INDEX idx_level2 (level2_category)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='策略分类维度表';
```

| 字段 | 类型 | 说明 |
|------|------|------|
| strategy_id | INT | 主键，自增 |
| level3_category | VARCHAR(100) | 三级分类（如"指增300"），唯一 |
| level2_category | VARCHAR(100) | 二级分类（如"指数增强"） |
| level1_category | VARCHAR(100) | 一级分类（如"股票策略"） |

**策略分类数据**:

| level1_category | level2_category | level3_category |
|-----------------|-----------------|-----------------|
| 股票策略 | 指数增强 | 指增300 |
| 股票策略 | 指数增强 | 指增500 |
| 股票策略 | 指数增强 | 指增1000 |
| 股票策略 | 指数增强 | 其他指增 |
| 股票策略 | 量化选股 | 量化选股 |
| 股票策略 | 主观股票 | 主观股票 |
| 股票策略 | 中性策略 | 中性策略 |
| 商品策略 | 量化CTA | 量化商品 |
| 商品策略 | 主观CTA | 主观商品 |
| 套利策略 | 商品套利 | 量化商品套利 |
| 套利策略 | 商品套利 | 主观商品套利 |
| 套利策略 | 期权套利 | 期权套利 |
| 套利策略 | ETF套利 | ETF套利 |
| 套利策略 | 股指套利 | 股指套利 |
| 套利策略 | 多策略套利 | 多策略套利 |
| 固收策略 | 纯债 | 固收 |
| 固收策略 | 固收增强 | 固收+ |
| 固收策略 | 债券复合 | 债券复合 |
| 固收策略 | 转债 | 转债策略 |
| 宏观策略 | 宏观策略 | 宏观策略 |
| 多策略 | 多策略 | 多策略 |
| 多策略 | FOF | FOF |

### 3. funds - 基金产品表

存储基金产品基本信息。

```sql
CREATE TABLE funds (
    fund_code VARCHAR(50) PRIMARY KEY COMMENT '产品代码',
    fund_name VARCHAR(300) NOT NULL COMMENT '产品名称',
    manager_id INT COMMENT '管理人ID',
    strategy_id INT COMMENT '策略ID',
    launch_date DATE COMMENT '成立日期',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_fund_name (fund_name),
    INDEX idx_manager (manager_id),
    INDEX idx_strategy (strategy_id),
    FOREIGN KEY (manager_id) REFERENCES managers(manager_id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='产品主表';
```

| 字段 | 类型 | 说明 |
|------|------|------|
| fund_code | VARCHAR(50) | 主键，产品代码 |
| fund_name | VARCHAR(300) | 产品名称 |
| manager_id | INT | 外键，关联管理人 |
| strategy_id | INT | 外键，关联策略 |
| launch_date | DATE | 产品成立日期 |

**产品代码说明**:
- 正式代码：如 `HF0000XXXX`（来自1205 Excel）
- 临时代码：如 `TMP_XXXXXXXX`（无法匹配时自动生成）

### 4. fund_performance - 业绩时间序列表

存储基金每周的业绩数据，支持27个业绩指标。

```sql
CREATE TABLE fund_performance (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',
    fund_code VARCHAR(50) NOT NULL COMMENT '产品代码',
    report_date DATE NOT NULL COMMENT '报告日期',
    data_source VARCHAR(20) DEFAULT 'excel' COMMENT '数据来源',

    -- 近一周
    weekly_excess DECIMAL(10,6) COMMENT '近一周超额',
    weekly_return DECIMAL(10,6) COMMENT '近一周收益率',

    -- 近一月
    monthly_excess DECIMAL(10,6) COMMENT '近一月超额',
    monthly_return DECIMAL(10,6) COMMENT '近一月收益率',
    monthly_max_drawdown DECIMAL(10,6) COMMENT '近一月最大回撤',

    -- 近三月
    quarterly_excess DECIMAL(10,6) COMMENT '近三月超额',
    quarterly_return DECIMAL(10,6) COMMENT '近三月收益率',
    quarterly_max_drawdown DECIMAL(10,6) COMMENT '近三月最大回撤',

    -- 近六月（年化）
    semi_annual_excess DECIMAL(10,6) COMMENT '近六月超额(年化)',
    semi_annual_return DECIMAL(10,6) COMMENT '近六月收益率(年化)',
    semi_annual_max_drawdown DECIMAL(10,6) COMMENT '近六月最大回撤',

    -- 近一年（年化）
    annual_excess DECIMAL(10,6) COMMENT '近一年超额(年化)',
    annual_return_ytd DECIMAL(10,6) COMMENT '近一年收益率(年化)',
    annual_max_drawdown DECIMAL(10,6) COMMENT '近一年最大回撤',

    -- 今年以来
    ytd_excess DECIMAL(10,6) COMMENT '今年以来超额',
    ytd_return DECIMAL(10,6) COMMENT '今年以来收益率',
    ytd_max_drawdown DECIMAL(10,6) COMMENT '今年以来最大回撤',

    -- 成立以来
    annual_return DECIMAL(10,6) COMMENT '成立以来年化收益率',
    cumulative_return DECIMAL(12,6) COMMENT '成立以来累计收益',
    max_drawdown DECIMAL(10,6) COMMENT '成立以来最大回撤',
    annual_volatility DECIMAL(10,6) COMMENT '成立以来年化波动率',

    -- 风险调整指标 - 近一年
    annual_sharpe DECIMAL(8,4) COMMENT '近一年夏普比率',
    annual_calmar DECIMAL(8,4) COMMENT '近一年卡玛比率',
    annual_sortino DECIMAL(8,4) COMMENT '近一年索提诺比率',

    -- 风险调整指标 - 成立以来
    inception_sharpe DECIMAL(8,4) COMMENT '成立以来夏普比率',
    inception_calmar DECIMAL(8,4) COMMENT '成立以来卡玛比率',
    inception_sortino DECIMAL(8,4) COMMENT '成立以来索提诺比率',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    UNIQUE KEY uk_fund_date (fund_code, report_date),
    INDEX idx_report_date (report_date),
    INDEX idx_annual_return (annual_return),
    INDEX idx_cumulative_return (cumulative_return),
    FOREIGN KEY (fund_code) REFERENCES funds(fund_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='业绩时间序列表';
```

**业绩指标分类**:

| 分类 | 字段 | 说明 |
|------|------|------|
| 周度 | weekly_return, weekly_excess | 近一周收益/超额 |
| 月度 | monthly_return, monthly_excess, monthly_max_drawdown | 近一月指标 |
| 季度 | quarterly_return, quarterly_excess, quarterly_max_drawdown | 近三月指标 |
| 半年 | semi_annual_return, semi_annual_excess, semi_annual_max_drawdown | 近六月指标（年化） |
| 年度 | annual_return_ytd, annual_excess, annual_max_drawdown | 近一年指标（年化） |
| 今年以来 | ytd_return, ytd_excess, ytd_max_drawdown | 今年以来指标 |
| 成立以来 | annual_return, cumulative_return, max_drawdown, annual_volatility | 成立以来指标 |
| 风险调整(年) | annual_sharpe, annual_calmar, annual_sortino | 近一年风险调整指标 |
| 风险调整(成立) | inception_sharpe, inception_calmar, inception_sortino | 成立以来风险调整指标 |

**数据存储格式**:
- 收益率/回撤：小数形式，如 0.1234 表示 12.34%
- 比率：直接数值，如夏普比率 2.15

### 5. report_metadata - 报告元数据表

存储每期周报的元数据信息。

```sql
CREATE TABLE report_metadata (
    report_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '报告ID',
    report_date DATE NOT NULL UNIQUE COMMENT '报告日期',
    pdf_filename VARCHAR(300) COMMENT 'PDF文件名',
    excel_filename VARCHAR(300) COMMENT 'Excel文件名',
    total_funds INT COMMENT '基金总数',
    total_strategies INT COMMENT '策略总数',
    parse_status VARCHAR(20) DEFAULT 'pending' COMMENT '解析状态',
    error_log TEXT COMMENT '错误日志',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='报告元数据表';
```

| 字段 | 类型 | 说明 |
|------|------|------|
| report_id | INT | 主键，自增 |
| report_date | DATE | 报告日期，唯一 |
| pdf_filename | VARCHAR(300) | PDF文件名 |
| excel_filename | VARCHAR(300) | Excel文件名 |
| total_funds | INT | 该期报告的基金总数 |
| total_strategies | INT | 该期报告的策略总数 |
| parse_status | VARCHAR(20) | 解析状态：pending/processing/completed/failed |
| error_log | TEXT | 解析错误日志 |

## 索引设计

### 主要索引

| 表 | 索引名 | 字段 | 类型 | 用途 |
|-----|--------|------|------|------|
| managers | PRIMARY | manager_id | 主键 | - |
| managers | manager_name | manager_name | 唯一 | 按名称查询 |
| strategies | PRIMARY | strategy_id | 主键 | - |
| strategies | level3_category | level3_category | 唯一 | 按策略名查询 |
| strategies | idx_level1 | level1_category | 普通 | 按一级分类筛选 |
| strategies | idx_level2 | level2_category | 普通 | 按二级分类筛选 |
| funds | PRIMARY | fund_code | 主键 | - |
| funds | idx_fund_name | fund_name | 普通 | 按名称搜索 |
| funds | idx_manager | manager_id | 普通 | 按管理人筛选 |
| funds | idx_strategy | strategy_id | 普通 | 按策略筛选 |
| fund_performance | PRIMARY | id | 主键 | - |
| fund_performance | uk_fund_date | fund_code, report_date | 唯一 | 防止重复数据 |
| fund_performance | idx_report_date | report_date | 普通 | 按日期查询 |
| fund_performance | idx_annual_return | annual_return | 普通 | 按收益排序 |

## 数据完整性

### 外键约束

```sql
-- funds 表外键
ALTER TABLE funds
ADD CONSTRAINT fk_funds_manager FOREIGN KEY (manager_id) REFERENCES managers(manager_id),
ADD CONSTRAINT fk_funds_strategy FOREIGN KEY (strategy_id) REFERENCES strategies(strategy_id);

-- fund_performance 表外键
ALTER TABLE fund_performance
ADD CONSTRAINT fk_performance_fund FOREIGN KEY (fund_code) REFERENCES funds(fund_code);
```

### 唯一约束

- `managers.manager_name` - 管理人名称唯一
- `strategies.level3_category` - 三级策略名称唯一
- `funds.fund_code` - 产品代码唯一
- `fund_performance(fund_code, report_date)` - 同一产品同一日期只有一条记录
- `report_metadata.report_date` - 报告日期唯一

## 常用查询示例

### 1. 获取某日期的基金业绩排名

```sql
SELECT
    f.fund_code,
    f.fund_name,
    m.manager_name,
    s.level3_category AS strategy_name,
    p.annual_return,
    p.cumulative_return,
    p.max_drawdown,
    p.annual_sharpe
FROM fund_performance p
JOIN funds f ON p.fund_code = f.fund_code
LEFT JOIN managers m ON f.manager_id = m.manager_id
LEFT JOIN strategies s ON f.strategy_id = s.strategy_id
WHERE p.report_date = '2025-12-19'
ORDER BY p.annual_return DESC
LIMIT 50;
```

### 2. 按策略统计基金数量

```sql
SELECT
    s.level1_category,
    s.level2_category,
    s.level3_category,
    COUNT(DISTINCT p.fund_code) AS fund_count
FROM strategies s
LEFT JOIN funds f ON s.strategy_id = f.strategy_id
LEFT JOIN fund_performance p ON f.fund_code = p.fund_code AND p.report_date = '2025-12-19'
GROUP BY s.strategy_id
ORDER BY fund_count DESC;
```

### 3. 搜索基金产品

```sql
SELECT
    f.fund_code,
    f.fund_name,
    m.manager_name,
    s.level3_category AS strategy_name,
    p.*
FROM funds f
JOIN fund_performance p ON f.fund_code = p.fund_code
LEFT JOIN managers m ON f.manager_id = m.manager_id
LEFT JOIN strategies s ON f.strategy_id = s.strategy_id
WHERE p.report_date = '2025-12-19'
  AND (f.fund_name LIKE '%量化%' OR m.manager_name LIKE '%量化%')
ORDER BY p.annual_return DESC
LIMIT 20;
```

### 4. 获取基金历史业绩

```sql
SELECT
    report_date,
    weekly_return,
    monthly_return,
    annual_return,
    cumulative_return,
    max_drawdown
FROM fund_performance
WHERE fund_code = 'HF000001'
ORDER BY report_date;
```

## 数据维护

### 清理测试数据

```sql
-- 清空所有业绩数据
TRUNCATE TABLE fund_performance;

-- 清空所有基金数据（需先清空业绩）
DELETE FROM funds;

-- 清空管理人数据
DELETE FROM managers;

-- 清空策略数据
DELETE FROM strategies;

-- 清空报告元数据
DELETE FROM report_metadata;
```

### 重建表结构

```python
from src.database.connection import drop_all_tables, init_db

# 删除所有表
drop_all_tables()

# 重新创建表
init_db()
```

## 性能优化建议

1. **分区表**: 如果数据量增长较大，可考虑按 `report_date` 对 `fund_performance` 表进行分区
2. **读写分离**: 高并发场景下可配置主从复制
3. **缓存**: 对热点查询（如排名、统计）添加 Redis 缓存
4. **归档**: 定期归档历史数据到归档表
