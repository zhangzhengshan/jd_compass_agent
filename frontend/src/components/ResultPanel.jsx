import React from 'react'

function splitQuestions(reportText) {
  if (!reportText) return []
  const lines = reportText.split('\n').map((line) => line.trim())
  const startIndex = lines.findIndex((line) => /^##\s*面试追问/.test(line))
  if (startIndex === -1) return []

  const items = []
  for (let i = startIndex + 1; i < lines.length; i += 1) {
    const line = lines[i]
    if (/^##\s+/.test(line)) break
    if (line.startsWith('- ')) items.push(line.slice(2).trim())
  }
  return items
}

function sectionLines(reportText, headingRegex) {
  if (!reportText) return []
  const lines = reportText.split('\n').map((line) => line.trim())
  const startIndex = lines.findIndex((line) => headingRegex.test(line))
  if (startIndex === -1) return []

  const items = []
  for (let i = startIndex + 1; i < lines.length; i += 1) {
    const line = lines[i]
    if (/^##\s+/.test(line)) break
    if (line.startsWith('- ')) items.push(line.slice(2).trim())
  }
  return items
}

function ResultPanel({ report, finalData }) {
  const parseResult = finalData?.parse_result || {}
  const routeResult = finalData?.route_result || {}
  const researchNotes = finalData?.research_notes || ''
  const jdSkills = finalData?.jd_skills || parseResult?.jd_keywords || []
  const resumeSkills = finalData?.resume_skills || parseResult?.resume_keywords || []
  const interviewQuestions = splitQuestions(report)
  const gaps = parseResult?.resume_gaps || []
  const suggestions = sectionLines(report, /^##\s*简历修改建议/)
  const finalAdvice = sectionLines(report, /^##\s*最终建议/)

  return (
    <section className="panel panel--result">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">结果展示区</p>
          <h2 className="panel__title">分析卡片 / 差距 / 题目 / 建议</h2>
        </div>
        <div className="badge badge--strong">
          {routeResult?.score !== undefined ? `匹配度 ${routeResult.score}/100` : '等待结果'}
        </div>
      </div>

      <div className="result-grid">
        <article className="result-card">
          <div className="result-card__label">匹配判断</div>
          <div className="result-card__value">{routeResult?.fit_level || '待生成'}</div>
          <div className="result-card__meta">路由：{routeResult?.route_label || '未生成'}</div>
        </article>

        <article className="result-card">
          <div className="result-card__label">核心缺口</div>
          <div className="result-card__value">{routeResult?.core_gap || '暂无'}</div>
          <div className="result-card__meta">下一步：{routeResult?.next_action || '等待分析'}</div>
        </article>

        <article className="result-card">
          <div className="result-card__label">研究分支</div>
          <div className="result-card__value">{researchNotes ? '已补充' : '未进入'}</div>
          <div className="result-card__meta">
            {researchNotes ? '包含公司/岗位补充信息' : '当前流程未触发研究节点'}
          </div>
        </article>
      </div>

      <div className="stack">
        <div className="section-block">
          <div className="section-block__title">技能对比</div>
          <div className="chip-group">
            {jdSkills.length ? (
              jdSkills.map((item, index) => (
                <span key={`jd-${index}`} className="chip chip--need">{item}</span>
              ))
            ) : (
              <span className="muted">无</span>
            )}
          </div>
          <div className="chip-group">
            {resumeSkills.length ? (
              resumeSkills.map((item, index) => (
                <span key={`resume-${index}`} className="chip chip--have">{item}</span>
              ))
            ) : (
              <span className="muted">无</span>
            )}
          </div>
        </div>

        <div className="section-block">
          <div className="section-block__title">匹配差距</div>
          <ul className="bullet-list">
            {gaps.length ? (
              gaps.map((item, index) => <li key={`gap-${index}`}>{item}</li>)
            ) : (
              <li className="muted">暂无明显缺口</li>
            )}
          </ul>
        </div>

        <div className="section-block">
          <div className="section-block__title">面试题</div>
          <ul className="bullet-list">
            {interviewQuestions.length ? (
              interviewQuestions.map((item, index) => <li key={`q-${index}`}>{item}</li>)
            ) : (
              <li className="muted">报告生成后会自动抽取面试追问</li>
            )}
          </ul>
        </div>

        <div className="section-block">
          <div className="section-block__title">最终建议</div>
          <ul className="bullet-list">
            {finalAdvice.length ? (
              finalAdvice.map((item, index) => <li key={`advice-${index}`}>{item}</li>)
            ) : suggestions.length ? (
              suggestions.map((item, index) => <li key={`suggestion-${index}`}>{item}</li>)
            ) : (
              <li className="muted">等待最终报告</li>
            )}
          </ul>
        </div>

        <div className="section-block">
          <div className="section-block__title">最终 Markdown 报告</div>
          <pre className="report-pre">{report || '这里会显示最终 Markdown 报告。'}</pre>
        </div>
      </div>
    </section>
  )
}

export default ResultPanel
