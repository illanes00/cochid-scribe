'use client'

import { useState, useEffect, useMemo } from 'react'
import Link from 'next/link'
import { useParams, useRouter } from 'next/navigation'
import {
  ChevronLeft,
  Download,
  Trash2,
  Table,
  BarChart3,
  LineChart,
  PieChart,
} from 'lucide-react'
import {
  BarChart,
  Bar,
  LineChart as RechartsLineChart,
  Line,
  PieChart as RechartsPieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Dataset, datasetsApi, chartsApi, ChartCreate } from '@/lib/api'

const CHART_COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4']

type ViewMode = 'table' | 'chart'
type ChartType = 'bar' | 'line' | 'pie'

export default function DatasetPage() {
  const params = useParams()
  const router = useRouter()
  const slug = params.slug as string

  const [dataset, setDataset] = useState<Dataset | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('table')
  const [chartType, setChartType] = useState<ChartType>('bar')
  const [xColumn, setXColumn] = useState<string>('')
  const [yColumn, setYColumn] = useState<string>('')
  const [savingChart, setSavingChart] = useState(false)

  // Load dataset
  useEffect(() => {
    async function loadDataset() {
      try {
        setLoading(true)
        const data = await datasetsApi.get(slug)
        setDataset(data)

        // Set default columns for chart
        if (data.columns.length >= 2) {
          const stringCol = data.columns.find(c => c.type === 'string')
          const numberCol = data.columns.find(c => c.type === 'number')
          if (stringCol) setXColumn(stringCol.name)
          if (numberCol) setYColumn(numberCol.name)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dataset')
      } finally {
        setLoading(false)
      }
    }
    loadDataset()
  }, [slug])

  // Prepare chart data
  const chartData = useMemo(() => {
    if (!dataset || !xColumn || !yColumn) return []
    return dataset.data.slice(0, 50).map(row => ({
      name: String(row[xColumn] || ''),
      value: Number(row[yColumn]) || 0,
    }))
  }, [dataset, xColumn, yColumn])

  async function handleDelete() {
    if (!confirm('Delete this dataset? This cannot be undone.')) return

    try {
      await datasetsApi.delete(slug)
      router.push('/data')
    } catch (err) {
      alert('Failed to delete dataset')
    }
  }

  async function handleSaveChart() {
    if (!dataset || !xColumn || !yColumn) return

    try {
      setSavingChart(true)
      const chartData: ChartCreate = {
        title: `${dataset.name} - ${yColumn} by ${xColumn}`,
        chart_type: chartType,
        dataset_id: dataset.id,
        config: {
          x_column: xColumn,
          y_column: yColumn,
        },
      }
      await chartsApi.create(chartData)
      alert('Chart saved successfully!')
    } catch (err) {
      alert('Failed to save chart')
    } finally {
      setSavingChart(false)
    }
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-muted">Loading dataset...</div>
      </div>
    )
  }

  if (error || !dataset) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg">
        <div className="text-center">
          <p className="text-c-red mb-4">{error || 'Dataset not found'}</p>
          <Link href="/data" className="text-c-blue hover:underline">
            Back to Data
          </Link>
        </div>
      </div>
    )
  }

  const numericColumns = dataset.columns.filter(c => c.type === 'number')

  return (
    <div className="h-screen flex flex-col bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper flex-shrink-0">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link href="/data" className="text-muted hover:text-ink">
              <ChevronLeft size={20} />
            </Link>
            <div>
              <h1 className="text-lg font-semibold">{dataset.name}</h1>
              <p className="text-xs text-muted">
                {dataset.row_count} rows &middot; {dataset.columns.length} columns
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button className="btn btn-sm">
              <Download size={14} className="mr-1" />
              Export
            </button>
            <button onClick={handleDelete} className="btn btn-sm text-c-red">
              <Trash2 size={14} />
            </button>
          </div>
        </div>

        {/* View mode tabs */}
        <div className="flex px-4 border-t border-line">
          <button
            onClick={() => setViewMode('table')}
            className={`flex items-center gap-2 px-4 py-2 text-sm border-b-2 ${
              viewMode === 'table'
                ? 'border-c-blue text-c-blue'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <Table size={14} />
            Table
          </button>
          <button
            onClick={() => setViewMode('chart')}
            className={`flex items-center gap-2 px-4 py-2 text-sm border-b-2 ${
              viewMode === 'chart'
                ? 'border-c-blue text-c-blue'
                : 'border-transparent text-muted hover:text-ink'
            }`}
          >
            <BarChart3 size={14} />
            Chart
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 overflow-hidden">
        {viewMode === 'table' ? (
          <div className="h-full overflow-auto">
            <table className="w-full border-collapse">
              <thead className="bg-paper sticky top-0">
                <tr>
                  {dataset.columns.map((col) => (
                    <th
                      key={col.name}
                      className="px-4 py-2 text-left text-sm font-medium text-ink border-b border-line whitespace-nowrap"
                    >
                      {col.name}
                      <span className="ml-1 text-xs text-muted">({col.type})</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {dataset.data.slice(0, 100).map((row, i) => (
                  <tr key={i} className="hover:bg-paper">
                    {dataset.columns.map((col) => (
                      <td
                        key={col.name}
                        className="px-4 py-2 text-sm border-b border-line whitespace-nowrap"
                      >
                        {row[col.name] != null ? String(row[col.name]) : '-'}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
            {dataset.data.length > 100 && (
              <div className="p-4 text-center text-sm text-muted bg-paper">
                Showing first 100 of {dataset.data.length} rows
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex">
            {/* Chart area */}
            <div className="flex-1 p-4">
              {xColumn && yColumn && chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  {chartType === 'bar' ? (
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="value" fill={CHART_COLORS[0]} name={yColumn} />
                    </BarChart>
                  ) : chartType === 'line' ? (
                    <RechartsLineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="value" stroke={CHART_COLORS[0]} name={yColumn} />
                    </RechartsLineChart>
                  ) : (
                    <RechartsPieChart>
                      <Pie
                        data={chartData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={150}
                        label
                      >
                        {chartData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </RechartsPieChart>
                  )}
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-muted">
                  Select columns to visualize
                </div>
              )}
            </div>

            {/* Chart config sidebar */}
            <aside className="w-64 border-l border-line bg-paper p-4 overflow-y-auto">
              <h3 className="font-medium mb-4">Chart Settings</h3>

              {/* Chart type */}
              <div className="mb-4">
                <label className="text-sm text-muted mb-2 block">Type</label>
                <div className="flex gap-1">
                  <button
                    onClick={() => setChartType('bar')}
                    className={`p-2 ${chartType === 'bar' ? 'bg-bg text-ink' : 'text-muted hover:bg-bg'}`}
                    title="Bar Chart"
                  >
                    <BarChart3 size={16} />
                  </button>
                  <button
                    onClick={() => setChartType('line')}
                    className={`p-2 ${chartType === 'line' ? 'bg-bg text-ink' : 'text-muted hover:bg-bg'}`}
                    title="Line Chart"
                  >
                    <LineChart size={16} />
                  </button>
                  <button
                    onClick={() => setChartType('pie')}
                    className={`p-2 ${chartType === 'pie' ? 'bg-bg text-ink' : 'text-muted hover:bg-bg'}`}
                    title="Pie Chart"
                  >
                    <PieChart size={16} />
                  </button>
                </div>
              </div>

              {/* X axis */}
              <div className="mb-4">
                <label className="text-sm text-muted mb-2 block">
                  {chartType === 'pie' ? 'Categories' : 'X Axis'}
                </label>
                <select
                  value={xColumn}
                  onChange={(e) => setXColumn(e.target.value)}
                  className="input w-full text-sm"
                >
                  <option value="">Select column</option>
                  {dataset.columns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Y axis */}
              <div className="mb-4">
                <label className="text-sm text-muted mb-2 block">
                  {chartType === 'pie' ? 'Values' : 'Y Axis'}
                </label>
                <select
                  value={yColumn}
                  onChange={(e) => setYColumn(e.target.value)}
                  className="input w-full text-sm"
                >
                  <option value="">Select column</option>
                  {numericColumns.map((col) => (
                    <option key={col.name} value={col.name}>
                      {col.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Save chart */}
              <button
                onClick={handleSaveChart}
                disabled={!xColumn || !yColumn || savingChart}
                className="btn btn-primary w-full"
              >
                {savingChart ? 'Saving...' : 'Save Chart'}
              </button>
            </aside>
          </div>
        )}
      </div>
    </div>
  )
}
