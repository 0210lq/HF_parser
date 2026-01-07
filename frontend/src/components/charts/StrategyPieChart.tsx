import ReactECharts from 'echarts-for-react'
import type { StrategyDistribution } from '@/lib/api'

interface StrategyPieChartProps {
  data: StrategyDistribution[]
  title?: string
}

export function StrategyPieChart({ data, title = '策略分布' }: StrategyPieChartProps) {
  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'bold',
      },
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      type: 'scroll',
      orient: 'vertical',
      right: 10,
      top: 20,
      bottom: 20,
    },
    series: [
      {
        name: '产品数量',
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '55%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
          position: 'center',
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 16,
            fontWeight: 'bold',
          },
        },
        labelLine: {
          show: false,
        },
        data: data.slice(0, 10).map((item) => ({
          value: item.value,
          name: item.name.length > 15 ? item.name.substring(0, 15) + '...' : item.name,
        })),
      },
    ],
  }

  return (
    <ReactECharts
      option={option}
      style={{ height: '400px', width: '100%' }}
    />
  )
}
