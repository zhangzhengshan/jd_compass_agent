import React from 'react'

const STEP_META = [
  { node: 'parse_node', label: '需求解析' },
  { node: 'route_node', label: '路由判断' },
  { node: 'research_node', label: '研究分支' },
  { node: 'compose_node', label: '结果生成' },
]

function latestEventForNode(events, node) {
  for (let i = events.length - 1; i >= 0; i -= 1) {
    if (events[i]?.node === node) return events[i]
  }
  return null
}

function statusLabel(status) {
  if (status === 'done') return '已完成'
  if (status === 'running') return '进行中'
  if (status === 'queued') return '等待中'
  if (status === 'skipped') return '已跳过'
  return '未开始'
}

function FlowTimeline({ events, loading, routeResult, routeLabel }) {
  const timeline = STEP_META.map((item, index) => {
    const last = latestEventForNode(events, item.node)
    let status = 'pending'

    if (last?.type === 'node_start') status = 'running'
    if (last?.type === 'node_end' || last?.type === 'final') status = 'done'
    if (loading && !last && index === 0) status = 'queued'
    if (item.node === 'research_node' && routeLabel === 'direct') status = 'skipped'

    return { ...item, status }
  })

  const didResearch = Boolean(
    events.some((event) => event?.node === 'research_node') ||
      routeLabel === 'revise' ||
      routeResult?.route_label === 'revise',
  )

  return (
    <section className="panel panel--timeline">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">流程展示区</p>
          <h2 className="panel__title">当前执行节点</h2>
        </div>
        <div className="badge badge--soft">{didResearch ? '已走研究分支' : '直接输出'}</div>
      </div>

      <div className="timeline">
        {timeline.map((item) => (
          <div key={item.node} className={`timeline-card timeline-card--${item.status}`}>
            <div className="timeline-card__main">
              <strong>{item.label}</strong>
              <span>{item.node}</span>
            </div>
            <div className="timeline-card__state">{statusLabel(item.status)}</div>
          </div>
        ))}
      </div>

      <div className="branch-box">
        <div className="branch-box__title">分支状态</div>
        <div className="branch-box__content">
          {routeResult?.routing_summary
            ? routeResult.routing_summary
            : routeLabel
              ? `当前路由：${routeLabel}`
              : '等待路由结果'}
        </div>
      </div>

      <div className="event-feed">
        <div className="event-feed__title">运行日志</div>
        <div className="event-feed__list">
          {events.length === 0 ? (
            <p className="muted">提交请求后，这里会实时显示节点事件。</p>
          ) : (
            events.map((event, index) => (
              <div key={`${event.type}-${event.node}-${index}`} className="event-row">
                <span className={`event-row__tag event-row__tag--${event.type}`}>{event.type}</span>
                <span className="event-row__node">{event.node}</span>
                <span className="event-row__message">{event.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </section>
  )
}

export default FlowTimeline
