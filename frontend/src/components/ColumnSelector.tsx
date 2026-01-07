import { useState, useEffect } from 'react'
import { Settings } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  PERFORMANCE_COLUMNS,
  COLUMN_CATEGORIES,
  getDefaultVisibleColumns,
  getColumnsByCategory
} from '@/lib/columnConfig'

interface ColumnSelectorProps {
  visibleColumns: string[]
  onColumnsChange: (columns: string[]) => void
}

export function ColumnSelector({ visibleColumns, onColumnsChange }: ColumnSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const columnsByCategory = getColumnsByCategory()

  const toggleColumn = (columnKey: string) => {
    // 基本信息列不可取消
    const column = PERFORMANCE_COLUMNS.find(col => col.key === columnKey)
    if (column?.category === 'basic') return

    if (visibleColumns.includes(columnKey)) {
      onColumnsChange(visibleColumns.filter(key => key !== columnKey))
    } else {
      onColumnsChange([...visibleColumns, columnKey])
    }
  }

  const selectAll = () => {
    onColumnsChange(PERFORMANCE_COLUMNS.map(col => col.key))
  }

  const resetToDefault = () => {
    onColumnsChange(getDefaultVisibleColumns())
  }

  return (
    <div className="relative">
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Settings className="h-4 w-4 mr-2" />
        列设置
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Popover */}
          <div className="absolute right-0 mt-2 w-96 bg-background border rounded-lg shadow-lg z-50 p-4 max-h-[500px] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">选择显示的列</h3>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={resetToDefault}>
                  重置
                </Button>
                <Button variant="ghost" size="sm" onClick={selectAll}>
                  全选
                </Button>
              </div>
            </div>

            {Object.entries(columnsByCategory).map(([category, columns]) => (
              <div key={category} className="mb-4">
                <h4 className="text-sm font-medium text-muted-foreground mb-2">
                  {COLUMN_CATEGORIES[category as keyof typeof COLUMN_CATEGORIES]}
                </h4>
                <div className="space-y-2">
                  {columns.map(column => (
                    <label
                      key={column.key}
                      className={`flex items-center space-x-2 text-sm cursor-pointer hover:bg-muted/50 p-1 rounded ${
                        column.category === 'basic' ? 'opacity-50 cursor-not-allowed' : ''
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={visibleColumns.includes(column.key)}
                        onChange={() => toggleColumn(column.key)}
                        disabled={column.category === 'basic'}
                        className="rounded border-gray-300"
                      />
                      <span>{column.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            ))}

            <div className="text-xs text-muted-foreground mt-4 pt-4 border-t">
              已选择 {visibleColumns.length} / {PERFORMANCE_COLUMNS.length} 列
            </div>
          </div>
        </>
      )}
    </div>
  )
}
