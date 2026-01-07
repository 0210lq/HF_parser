import React, { useState, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { ColumnSelector } from '@/components/ColumnSelector'
import { getFunds, getStrategies, type Fund, type Strategy } from '@/lib/api'
import { formatPercent, formatNumber } from '@/lib/utils'
import { PERFORMANCE_COLUMNS, getDefaultVisibleColumns } from '@/lib/columnConfig'
import { Search as SearchIcon, ChevronLeft, ChevronRight } from 'lucide-react'

const STORAGE_KEY = 'search_visible_columns'

export function Search() {
  const [keyword, setKeyword] = useState('')
  const [strategyId, setStrategyId] = useState<number | undefined>()
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('annual_return')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [visibleColumns, setVisibleColumns] = useState<string[]>(() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ? JSON.parse(stored) : getDefaultVisibleColumns()
  })
  const pageSize = 20

  // 保存列选择到localStorage
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns))
  }, [visibleColumns])

  const { data: strategies } = useQuery({
    queryKey: ['strategies'],
    queryFn: getStrategies,
  })

  const { data: fundsData, isLoading } = useQuery({
    queryKey: ['funds-search', keyword, strategyId, page, sortBy, sortOrder],
    queryFn: () => getFunds({
      keyword: keyword || undefined,
      strategy_id: strategyId,
      sort_by: sortBy,
      order: sortOrder,
      page,
      page_size: pageSize,
    }),
  })

  const handleSearch = () => {
    setPage(1)
  }

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')
    } else {
      setSortBy(field)
      setSortOrder('desc')
    }
    setPage(1)
  }

  const SortHeader = ({ field, children }: { field: string; children: React.ReactNode }) => {
    const column = PERFORMANCE_COLUMNS.find(col => col.key === field)
    const align = column?.category === 'basic' ? 'left' : 'right'

    return (
      <TableHead
        className={`${align === 'right' ? 'text-right' : ''} ${column?.sortable ? 'cursor-pointer hover:bg-muted/50 select-none' : ''}`}
        onClick={() => column?.sortable && handleSort(field)}
      >
        <div className={`flex items-center ${align === 'right' ? 'justify-end' : 'justify-start'} gap-1`}>
          {children}
          {column?.sortable && sortBy === field && (
            <span className="text-xs">{sortOrder === 'desc' ? '↓' : '↑'}</span>
          )}
        </div>
      </TableHead>
    )
  }

  // 获取单元格内容
  const getCellContent = (fund: Fund, columnKey: string) => {
    switch (columnKey) {
      case 'fund_name':
        return (
          <TableCell className="max-w-[180px] truncate" title={fund.fund_name}>
            {fund.fund_name}
          </TableCell>
        )
      case 'manager_name':
        return (
          <TableCell className="max-w-[120px] truncate" title={fund.manager_name || ''}>
            {fund.manager_name || '-'}
          </TableCell>
        )
      case 'strategy_name':
        return (
          <TableCell className="max-w-[120px] truncate" title={fund.strategy_name || ''}>
            {fund.strategy_name || '-'}
          </TableCell>
        )
      default:
        // 业绩数据字段
        const value = fund.latest_performance?.[columnKey as keyof typeof fund.latest_performance]
        const numValue = typeof value === 'number' ? value : null

        // 判断是否为比率字段（夏普、卡玛、索提诺）
        const isRatio = columnKey.includes('sharpe') || columnKey.includes('calmar') || columnKey.includes('sortino')

        // 收益类指标用红绿色，回撤和波动率用红色，比率不着色
        let colorClass = ''
        if (!isRatio && numValue !== null) {
          if (columnKey.includes('drawdown') || columnKey.includes('volatility')) {
            colorClass = 'text-red-600'
          } else {
            colorClass = numValue >= 0 ? 'text-green-600' : 'text-red-600'
          }
        }

        return (
          <TableCell className={`text-right ${colorClass}`}>
            {isRatio ? formatNumber(numValue) : formatPercent(numValue)}
          </TableCell>
        )
    }
  }

  // 获取可见列配置
  const visibleColumnConfigs = PERFORMANCE_COLUMNS.filter(col =>
    visibleColumns.includes(col.key)
  )

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">产品搜索</h1>

      {/* Search Filters */}
      <Card>
        <CardHeader>
          <CardTitle>筛选条件</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="搜索产品名称、管理人..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
              />
            </div>
            <select
              className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm"
              value={strategyId || ''}
              onChange={(e) => setStrategyId(e.target.value ? Number(e.target.value) : undefined)}
            >
              <option value="">全部策略</option>
              {strategies?.items?.map((s: Strategy) => (
                <option key={s.strategy_id} value={s.strategy_id}>
                  {s.strategy_name.length > 20 ? s.strategy_name.substring(0, 20) + '...' : s.strategy_name}
                  ({s.fund_count})
                </option>
              ))}
            </select>
            <Button onClick={handleSearch}>
              <SearchIcon className="h-4 w-4 mr-2" />
              搜索
            </Button>
          </div>
    </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between flex-wrap gap-4">
            <CardTitle>
              搜索结果
              {fundsData && (
                <span className="text-sm font-normal text-muted-foreground ml-2">
                  共 {fundsData.total} 条记录
                </span>
              )}
            </CardTitle>
            <ColumnSelector
              visibleColumns={visibleColumns}
              onColumnsChange={setVisibleColumns}
            />
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-32">加载中...</div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-12">序号</TableHead>
                      {visibleColumnConfigs.map(column => (
                        <SortHeader key={column.key} field={column.key}>
                          {column.label}
                        </SortHeader>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {fundsData?.items?.map((fund: Fund, index: number) => (
                      <TableRow key={fund.fund_code}>
                        <TableCell className="font-medium">
                          {(page - 1) * pageSize + index + 1}
                        </TableCell>
                        {visibleColumnConfigs.map(column => (
                          <React.Fragment key={column.key}>
                            {getCellContent(fund, column.key)}
                          </React.Fragment>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>

              {/* Pagination */}
              {fundsData && fundsData.total_pages > 1 && (
                <div className="flex items-center justify-between mt-4">
                  <div className="text-sm text-muted-foreground">
                    第 {page} / {fundsData.total_pages} 页
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      上一页
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage(p => Math.min(fundsData.total_pages, p + 1))}
                      disabled={page === fundsData.total_pages}
                    >
                  下一页
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
