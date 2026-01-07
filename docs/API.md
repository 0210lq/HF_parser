# API 接口文档

## 概述

HF Parser API 基于 FastAPI 构建，提供私募基金数据的查询、筛选和分析功能。

- **Base URL**: `http://localhost:8000/api`
- **API文档**: `http://localhost:8000/docs` (Swagger UI)
- **数据格式**: JSON

## 认证

当前版本无需认证，所有接口公开访问。

---

## 接口列表

### 1. 统计分析 (Analytics)

#### 1.1 获取统计概览

获取系统整体统计数据。

```
GET /api/analytics/stats
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| report_date | date | 否 | 报告日期，格式：YYYY-MM-DD |

**响应示例**:
```json
{
  "total_managers": 1434,
  "total_strategies": 23,
  "total_funds": 4076,
  "total_performances": 4076,
  "latest_report_date": "2025-12-19"
}
```

#### 1.2 获取可用报告日期

获取系统中所有可用的报告日期列表。

```
GET /api/analytics/report-dates
```

**响应示例**:
```json
{
  "dates": ["2025-12-19", "2025-12-12", "2025-12-05"]
}
```

#### 1.3 获取业绩排名

按指定指标获取基金业绩排名。

```
GET /api/analytics/ranking
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| metric | string | 否 | annual_return | 排名指标 |
| report_date | date | 否 | 最新日期 | 报告日期 |
| strategy_id | int | 否 | - | 策略ID筛选 |
| manager_id | int | 否 | - | 管理人ID筛选 |
| limit | int | 否 | 50 | 返回数量(1-200) |

**可用排名指标**:
- 收益类: `weekly_return`, `monthly_return`, `quarterly_return`, `annual_return`, `cumulative_return`
- 超额类: `weekly_excess`, `monthly_excess`, `annual_excess`
- 风险类: `max_drawdown`, `annual_volatility`
- 风险调整: `annual_sharpe`, `annual_calmar`, `annual_sortino`

**响应示例**:
```json
{
  "metric": "annual_return",
  "report_date": "2025-12-19",
  "items": [
    {
      "rank": 1,
      "fund_code": "HF000001",
      "fund_name": "示例基金1号",
      "manager_name": "示例资产",
      "strategy_name": "量化选股",
      "value": 0.4523,
      "report_date": "2025-12-19"
    }
  ],
  "total": 50
}
```

#### 1.4 获取策略分布

获取各策略的基金数量分布。

```
GET /api/analytics/strategy-distribution
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| report_date | date | 否 | 报告日期 |

**响应示例**:
```json
{
  "items": [
    {"name": "主观股票", "value": 1118},
    {"name": "多策略", "value": 415},
    {"name": "量化商品", "value": 388}
  ]
}
```

#### 1.5 多产品对比

对比多个基金产品的业绩指标。

```
POST /api/analytics/compare
```

**请求体**:
```json
{
  "fund_codes": ["HF000001", "HF000002", "HF000003"],
  "start_date": "2025-01-01",
  "end_date": "2025-12-19"
}
```

**响应示例**:
```json
{
  "funds": [
    {
      "fund_code": "HF000001",
      "fund_name": "示例基金1号",
      "manager_name": "示例资产",
      "strategy_name": "量化选股",
      "performances": [...],
      "latest": {
        "report_date": "2025-12-19",
        "annual_return": 0.2534,
        "cumulative_return": 0.8923,
        "max_drawdown": -0.1234,
        "annual_sharpe": 2.15
      }
    }
  ],
  "date_range": ["2025-12-05", "2025-12-12", "2025-12-19"]
}
```

---

### 2. 基金产品 (Funds)

#### 2.1 搜索基金

搜索和筛选基金产品，支持分页和排序。

```
GET /api/funds
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 搜索关键词（产品名称/管理人/代码） |
| manager_id | int | 否 | - | 管理人ID |
| strategy_id | int | 否 | - | 策略ID |
| min_annual_return | float | 否 | - | 最小年化收益 |
| max_annual_return | float | 否 | - | 最大年化收益 |
| max_drawdown | float | 否 | - | 最大回撤阈值 |
| min_sharpe | float | 否 | - | 最小夏普比率 |
| sort_by | string | 否 | annual_return | 排序字段 |
| order | string | 否 | desc | 排序方向(asc/desc) |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量(1-100) |
| report_date | date | 否 | 最新日期 | 报告日期 |

**可用排序字段**:
所有业绩指标字段均可用于排序，包括：
- `weekly_return`, `weekly_excess`
- `monthly_return`, `monthly_excess`, `monthly_max_drawdown`
- `quarterly_return`, `quarterly_max_drawdown`
- `semi_annual_return`, `semi_annual_excess`
- `annual_return`, `annual_return_ytd`, `annual_excess`
- `cumulative_return`, `max_drawdown`, `annual_volatility`
- `annual_sharpe`, `annual_calmar`, `annual_sortino`
- `inception_sharpe`, `inception_calmar`, `inception_sortino`

**响应示例**:
```json
{
  "items": [
    {
      "fund_code": "HF000001",
      "fund_name": "示例基金1号",
      "manager_id": 1,
      "manager_name": "示例资产",
      "strategy_id": 5,
      "strategy_name": "量化选股",
      "launch_date": "2020-01-15",
      "latest_performance": {
        "report_date": "2025-12-19",
        "weekly_return": 0.0123,
        "monthly_return": 0.0456,
        "quarterly_return": 0.1234,
        "annual_return": 0.2534,
        "cumulative_return": 0.8923,
        "max_drawdown": -0.1234,
        "annual_volatility": 0.1567,
        "annual_sharpe": 2.15,
        "annual_calmar": 3.45,
        "annual_sortino": 4.56
      }
    }
  ],
  "total": 4076,
  "page": 1,
  "page_size": 20,
  "total_pages": 204
}
```

#### 2.2 获取基金详情

获取单个基金的详细信息。

```
GET /api/funds/{fund_code}
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| fund_code | string | 基金代码 |

**响应示例**:
```json
{
  "fund_code": "HF000001",
  "fund_name": "示例基金1号",
  "manager_id": 1,
  "manager_name": "示例资产",
  "strategy_id": 5,
  "strategy_name": "量化选股",
  "launch_date": "2020-01-15",
  "latest_performance": {...}
}
```

#### 2.3 获取基金业绩历史

获取基金的历史业绩数据。

```
GET /api/funds/{fund_code}/performance
```

**路径参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| fund_code | string | 基金代码 |

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| start_date | date | 否 | 开始日期 |
| end_date | date | 否 | 结束日期 |

**响应示例**:
```json
{
  "items": [
    {
      "id": 1,
      "fund_code": "HF000001",
      "report_date": "2025-12-19",
      "weekly_return": 0.0123,
      "monthly_return": 0.0456,
      ...
    }
  ],
  "total": 10
}
```

---

### 3. 策略 (Strategies)

#### 3.1 获取策略列表

获取所有策略分类及其基金数量。

```
GET /api/strategies
```

**查询参数**:
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| report_date | date | 否 | 报告日期（用于统计基金数量） |

**响应示例**:
```json
{
  "items": [
    {
      "strategy_id": 1,
      "strategy_name": "指增300",
      "level1_category": "股票策略",
      "level2_category": "指数增强",
      "fund_count": 289
    },
    {
      "strategy_id": 2,
      "strategy_name": "指增500",
      "level1_category": "股票策略",
      "level2_category": "指数增强",
      "fund_count": 405
    }
  ],
  "total": 22
}
```

---

### 4. 管理人 (Managers)

#### 4.1 获取管理人列表

获取管理人列表，支持搜索和分页。

```
GET /api/managers
```

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| keyword | string | 否 | - | 搜索关键词 |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量 |

**响应示例**:
```json
{
  "items": [
    {
      "manager_id": 1,
      "manager_name": "示例资产",
      "establishment_date": "2015-06-01",
      "company_size": "50-100亿",
      "fund_count": 15
    }
  ],
  "total": 1434,
  "page": 1,
  "page_size": 20,
  "total_pages": 72
}
```

---

## 错误处理

### 错误响应格式

```json
{
  "detail": "错误描述信息"
}
```

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 数据类型说明

### 业绩指标字段

所有业绩指标均为小数形式（非百分比），例如：
- `0.1234` 表示 12.34%
- `-0.0567` 表示 -5.67%

### 日期格式

所有日期字段使用 ISO 8601 格式：`YYYY-MM-DD`

### 分页

分页响应包含以下字段：
- `items`: 数据列表
- `total`: 总记录数
- `page`: 当前页码
- `page_size`: 每页数量
- `total_pages`: 总页数

---

## 使用示例

### cURL

```bash
# 获取统计概览
curl http://localhost:8000/api/analytics/stats

# 搜索基金
curl "http://localhost:8000/api/funds?keyword=量化&strategy_id=5&sort_by=annual_return&order=desc"

# 获取策略列表
curl http://localhost:8000/api/strategies

# 多产品对比
curl -X POST http://localhost:8000/api/analytics/compare \
  -H "Content-Type: application/json" \
  -d '{"fund_codes": ["HF000001", "HF000002"]}'
```

### JavaScript (Axios)

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api'
});

// 获取基金列表
const getFunds = async (params) => {
  const { data } = await api.get('/funds', { params });
  return data;
};

// 使用示例
const funds = await getFunds({
  keyword: '量化',
  strategy_id: 5,
  sort_by: 'annual_return',
  order: 'desc',
  page: 1,
  page_size: 20
});
```

### Python (Requests)

```python
import requests

BASE_URL = 'http://localhost:8000/api'

# 获取统计概览
response = requests.get(f'{BASE_URL}/analytics/stats')
stats = response.json()

# 搜索基金
response = requests.get(f'{BASE_URL}/funds', params={
    'keyword': '量化',
    'strategy_id': 5,
    'sort_by': 'annual_return',
    'order': 'desc'
})
funds = response.json()
```
