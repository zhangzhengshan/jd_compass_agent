import { useMemo, useState } from 'react'
import React from 'react'; // 必须加上这一行
const API_URL = 'http://127.0.0.1:8000/api/run'

const defaultJD = `Python 后端实习生
岗位要求：
1. 熟悉 Python、FastAPI、SQL。
2. 有接口开发和基础工程经验。
3. 了解 LLM / Agent 优先。`

const defaultResume = `我做过 Python Web 项目，写过 FastAPI 接口，能使用 SQL。
项目中负责接口设计、数据处理与基础调试。`

const STEP_META = [
  { node: 'parse_node', label: '需求解析' },
  { node: 'route_node', label: '路由判断' },
  { node: 'research_node', label: '研究分支' },
  { node: 'compose_node', label: '输出生成' },
]

function latestEventForNode(events, node) {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    if (events[i]?.node === node) return events[i]
  }
  return null
}

function App() {
  const [jd, setJd] = useState(defaultJD)
  const [resume, setResume] = useState(defaultResume)
  const [company, setCompany] = useState('某互联网公司')
  const [extra, setExtra] = useState('请补充公司背景和岗位画像。')
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState([])
  const [report, setReport] = useState('')
  const [route, setRoute] = useState('')
  const [error, setError] = useState('')

  const timeline = useMemo(() => {
    return STEP_META.map((item) => {
      const last = latestEventForNode(events, item.node)
      let status = 'pending'

      if (last?.type === 'node_start') status = 'running'
      if (last?.type === 'node_end' || last?.type === 'final') status = 'done'
      if (loading && !last && item.node === 'parse_node') status = 'queued'

      return {
        ...item,
        status,
      }
    })
  }, [events, loading])

  const eventLog = useMemo(() => {
    return events.filter((e) => e && e.type !== 'final')
  }, [events])

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setEvents([])
    setReport('')
    setRoute('')
    setError('')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jd,
          resume,
          company,
          extra_requirements: extra,
        }),
      })

      if (!response.ok || !response.body) {
        throw new Error(`请求失败：${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder('utf-8')
      let buffer = ''

      while (true) {
        const { value, done } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (!line.trim()) continue
          const event = JSON.parse(line)
          setEvents((prev) => [...prev, event])

          if (event.type === 'final') {
            setReport(event.data?.final_report || '')
            setRoute(event.data?.route || '')
          }
        }
      }

      if (buffer.trim()) {
        const event = JSON.parse(buffer)
        setEvents((prev) => [...prev, event])
        if (event.type === 'final') {
          setReport(event.data?.final_report || '')
          setRoute(event.data?.route || '')
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setError(message)
      setEvents((prev) => [
        ...prev,
        { type: 'error', node: 'client', message, data: {} },
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">JD Compass Agent</p>
          <h1>简历分析助手展示页面</h1>
          <p className="subtle">
            最小闭环：前端输入 → 后端路由 → 结构化报告
          </p>
        </div>
        <div className="badge">{loading ? 'Running' : 'Ready'}</div>
      </header>

      <main className="grid">
        <section className="card">
          <h2>输入区</h2>
          <form onSubmit={handleSubmit} className="form">
            <label>
              岗位 JD
              <textarea
                value={jd}
                onChange={(e) => setJd(e.target.value)}
                rows={8}
                placeholder="粘贴岗位 JD"
              />
            </label>

            <label>
              简历
              <textarea
                value={resume}
                onChange={(e) => setResume(e.target.value)}
                rows={8}
                placeholder="粘贴你的简历内容"
              />
            </label>

            <div className="two-col">
              <label>
                公司名
                <input
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="例如：字节跳动"
                />
              </label>

              <label>
                额外要求
                <input
                  value={extra}
                  onChange={(e) => setExtra(e.target.value)}
                  placeholder="例如：请补充公司背景和岗位画像"
                />
              </label>
            </div>

            <button type="submit" disabled={loading}>
              {loading ? '执行中…' : '开始分析'}
            </button>

            {error ? <div className="error-box">错误：{error}</div> : null}
          </form>
        </section>

        <section className="card">
          <h2>流程状态</h2>
          <div className="timeline">
            {timeline.map((item) => (
              <div key={item.node} className={`timeline-item ${item.status}`}>
                <div className="timeline-title">
                  <strong>{item.label}</strong>
                  <span className="timeline-node">{item.node}</span>
                </div>
                <span className="timeline-status">
                  {item.status === 'done'
                    ? '已完成'
                    : item.status === 'running'
                      ? '进行中'
                      : item.status === 'queued'
                        ? '等待中'
                        : '未开始'}
                </span>
              </div>
            ))}
          </div>

          <h2 style={{ marginTop: 24 }}>运行日志</h2>
          <div className="log">
            {eventLog.length === 0 ? (
              <p className="muted">提交一次请求后，这里会实时显示节点事件。</p>
            ) : (
              eventLog.map((event, index) => (
                <div key={`${event.type}-${event.node}-${index}`} className={`log-line ${event.type}`}>
                  <span className="log-tag">{event.type}</span>
                  <span>{event.node}</span>
                  <span>{event.message}</span>
                </div>
              ))
            )}
          </div>
        </section>

        <section className="card result">
          <div className="result-header">
            <h2>最终报告</h2>
            <div className="route-pill">路由：{route || '未生成'}</div>
          </div>

          <pre>{report || '这里会显示最终 Markdown 报告。'}</pre>
        </section>
      </main>
    </div>
  )
}

export default App
