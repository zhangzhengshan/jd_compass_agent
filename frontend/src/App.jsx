import React, { useMemo, useState } from 'react'
import InputForm from './components/InputForm.jsx'
import FlowTimeline from './components/FlowTimeline.jsx'
import ResultPanel from './components/ResultPanel.jsx'

const API_URL = 'http://127.0.0.1:8000/api/run'

const defaultJD = `Python 后端实习生
岗位要求：
1. 熟悉 Python、FastAPI、SQL。
2. 有接口开发和基础工程经验。
3. 了解 LLM / Agent 优先。`

const defaultResume = `我做过 Python Web 项目，写过 FastAPI 接口，能使用 SQL。
项目中负责接口设计、数据处理与基础调试。`

function App() {
  const [jd, setJd] = useState(defaultJD)
  const [resume, setResume] = useState(defaultResume)
  const [company, setCompany] = useState('某互联网公司')
  const [extra, setExtra] = useState('请补充公司背景和岗位画像。')
  const [loading, setLoading] = useState(false)
  const [events, setEvents] = useState([])
  const [report, setReport] = useState('')
  const [finalData, setFinalData] = useState(null)
  const [error, setError] = useState('')

  const routeLabel = finalData?.route_result?.route_label || ''

  const statusText = useMemo(() => {
    if (loading) return 'Running'
    if (report) return 'Ready'
    return 'Idle'
  }, [loading, report])

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setEvents([])
    setReport('')
    setFinalData(null)
    setError('')

    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
            setFinalData(event.data || null)
          }
        }
      }

      if (buffer.trim()) {
        const event = JSON.parse(buffer)
        setEvents((prev) => [...prev, event])
        if (event.type === 'final') {
          setReport(event.data?.final_report || '')
          setFinalData(event.data || null)
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err)
      setError(message)
      setEvents((prev) => [...prev, { type: 'error', node: 'client', message, data: {} }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <header className="hero">
        <div>
          <p className="eyebrow">JD Compass Agent</p>
          <h1>轻量级多 Agent 求职分析助手</h1>
          <p className="subtle">固定主干 + 有限路由 + 流式展示，适合面试演示</p>
        </div>
        <div className={`badge ${loading ? 'badge--live' : 'badge--soft'}`}>{statusText}</div>
      </header>

      <main className="layout">
        <div className="layout__left">
          <InputForm
            jd={jd}
            resume={resume}
            company={company}
            extra={extra}
            loading={loading}
            error={error}
            onJdChange={setJd}
            onResumeChange={setResume}
            onCompanyChange={setCompany}
            onExtraChange={setExtra}
            onSubmit={handleSubmit}
            onFillExample={() => {
              setJd(defaultJD)
              setResume(defaultResume)
              setCompany('某互联网公司')
              setExtra('请补充公司背景和岗位画像。')
            }}
          />
        </div>

        <div className="layout__middle">
          <FlowTimeline
            events={events}
            loading={loading}
            routeResult={finalData?.route_result}
            routeLabel={routeLabel}
          />
        </div>

        <div className="layout__right">
          <ResultPanel report={report} finalData={finalData} />
        </div>
      </main>
    </div>
  )
}

export default App
