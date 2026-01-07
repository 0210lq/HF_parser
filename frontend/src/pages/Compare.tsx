import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import ReactECharts from 'echarts-for-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { getFunds, compareFunds, type Fund } from '@/lib/api'
import { formatPercent } from '@/lib/utils'
import { Plus, X, GitCompare, Search } from 'lucide-react'

export function Compare() {
  const [searchKeyword, setSearchKeyword] = useState('')
  const [selectedFunds, setSelectedFunds] = useState<Fund[]>([])
  const [showDropdown, setShowDropdown] = useState(false)

  const { data: searchResults, isLoading: isSearching } = useQuery({
    queryKey: ['funds-compare-search', searchKeyword],
    queryFn: () => getFunds({ keyword: searchKeyword || undefined, page_size: 10 }),
    enabled: showDropdown,
  })

  const { data: compareData, isLoading } = useQuery({
    queryKey: ['compare', selectedFunds.map(f => f.fund_code)],
    queryFn: () => compareFunds(selectedFunds.map(f => f.fund_code)),
    enabled: selectedFunds.length >= 2,
  })

  const addFund = (fund: Fund) => {
    if (selectedFunds.length < 5 && !selectedFunds.find(f => f.fund_code === fund.fund_code)) {
      setSelectedFunds([...selectedFunds, fund])
      setSearchKeyword('')
      setShowDropdown(false)
    }
  }

  const removeFund = (fundCode: string) => {
    setSelectedFunds(selectedFunds.filter(f => f.fund_code !== fundCode))
  }

  const handleInputFocus = () => {
    setShowDropdown(true)
  }

  const handleInputBlur = () => {
    // 延迟关闭，让点击事件先触发
    setTimeout(() => setShowDropdown(false), 200)
  }

  const getRadarOption = () => {
    if (!compareData?.funds?.length) return {}

    const indicators = [
      { name: '年化收益', max: 1 },
      { name: '夏普比率', max: 5 },
      { name: '累计收益', max: 2 },
      { name: '最大回撤', max: 0.5 },
      { name: '波动率', max: 0.5 },
    ]

    const series = compareData.funds.map((fund: any) => {
      const latest = fund.latest
      return {
        name: fund.fund_name.substring(0, 10),
        type: 'radar',
        data: [{
          value: [
            Math.abs(latest?.annual_return || 0),
            Math.abs(latest?.annual_sharpe || 0),
            Math.abs(latest?.cumulative_return || 0),
            Math.abs(latest?.max_drawdown || 0),
            Math.abs(latest?.annual_volatility || 0),
          ],
          name: fund.fund_name.substring(0, 10),
        }],
      }
    })

    return {
      tooltip: {},
      legend: {
        data: compareData.funds.map((f: any) => f.fund_name.substring(0, 10)),
        bottom: 0,
      },
      radar: {
        indicator: indicators,
        radius: '60%',
      },
      series,
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">产品对比</h1>

      {/* Fund Selector */}
      <Card>
        <CardHeader>
          <CardTitle>选择产品 (最多5个)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Selected Funds */}
            <div className="flex gap-2 flex-wrap">
              {selectedFunds.map(fund => (
                <div
                  key={fund.fund_code}
                  className="flex items-center gap-2 px-3 py-1 bg-secondary rounded-full text-sm"
                >
                  <span className="max-w-[150px] truncate">{fund.fund_name}</span>
                  <button
                    onClick={() => removeFund(fund.fund_code)}
                    className="hover:text-destructive"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              ))}
            </div>

            {/* Search Input */}
            {selectedFunds.length < 5 && (
              <div className="relative">
                <div className="flex gap-2">
                  <Input
                    placeholder="输入产品名称或管理人搜索..."
                    value={searchKeyword}
                    onChange={(e) => setSearchKeyword(e.target.value)}
                    onFocus={handleInputFocus}
                    onBlur={handleInputBlur}
                    className="flex-1"
                  />
                  <Button variant="outline" onClick={() => setShowDropdown(true)}>
                    <Search className="h-4 w-4" />
                  </Button>
                </div>
                {showDropdown && (
                  <div className="absolute z-10 w-full mt-1 bg-background border rounded-md shadow-lg max-h-60 overflow-auto">
                    {isSearching ? (
                      <div className="px-4 py-3 text-sm text-muted-foreground">搜索中...</div>
                    ) : searchResults?.items?.length > 0 ? (
                      searchResults.items
                        .filter((fund: Fund) => !selectedFunds.find(f => f.fund_code === fund.fund_code))
                        .map((fund: Fund) => (
                          <button
                            key={fund.fund_code}
                            className="w-full px-4 py-2 text-left hover:bg-muted flex items-center justify-between"
                            onClick={() => addFund(fund)}
                          >
                            <div className="flex-1 min-w-0">
                              <div className="truncate font-medium">{fund.fund_name}</div>
                              <div className="text-xs text-muted-foreground truncate">
                                {fund.manager_name} · {fund.strategy_name}
                              </div>
                            </div>
                            <Plus className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
                          </button>
                        ))
                    ) : (
                      <div className="px-4 py-3 text-sm text-muted-foreground">
                        {searchKeyword ? '未找到匹配的产品' : '输入关键词搜索，或直接点击选择'}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Comparison Results */}
      {selectedFunds.length >= 2 && (
        <>
          {/* Metrics Table */}
          <Card>
            <CardHeader>
              <CardTitle>指标对比</CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center h-32">加载中...</div>
              ) : compareData?.funds?.length ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>指标</TableHead>
                      {compareData.funds.map((fund: any) => (
                        <TableHead key={fund.fund_code} className="text-center">
                          <div className="max-w-[120px] truncate" title={fund.fund_name}>
                            {fund.fund_name}
                          </div>
                        </TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    <TableRow>
                      <TableCell className="font-medium">管理人</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center">
                          {fund.manager_name || '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">年化收益</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center text-green-600 font-medium">
                          {formatPercent(fund.latest?.annual_return)}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">累计收益</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center">
                          {formatPercent(fund.latest?.cumulative_return)}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">最大回撤</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center text-red-600">
                          {formatPercent(fund.latest?.max_drawdown)}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">年化夏普</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center">
                          {fund.latest?.annual_sharpe?.toFixed(2) || '-'}
                        </TableCell>
                      ))}
                    </TableRow>
                    <TableRow>
                      <TableCell className="font-medium">年化波动率</TableCell>
                      {compareData.funds.map((fund: any) => (
                        <TableCell key={fund.fund_code} className="text-center">
                          {formatPercent(fund.latest?.annual_volatility)}
                        </TableCell>
                      ))}
                    </TableRow>
                  </TableBody>
                </Table>
              ) : null}
            </CardContent>
          </Card>

          {/* Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>雷达图对比</CardTitle>
            </CardHeader>
            <CardContent>
              {compareData?.funds?.length && (
                <ReactECharts
                  option={getRadarOption()}
                  style={{ height: '400px', width: '100%' }}
                />
              )}
            </CardContent>
          </Card>
        </>
      )}

      {selectedFunds.length < 2 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center h-64 text-muted-foreground">
            <GitCompare className="h-12 w-12 mb-4" />
            <p>请选择至少2个产品进行对比</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
