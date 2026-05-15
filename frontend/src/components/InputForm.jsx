import React from 'react'

function InputForm({
  jd,
  resume,
  company,
  extra,
  loading,
  error,
  onJdChange,
  onResumeChange,
  onCompanyChange,
  onExtraChange,
  onSubmit,
  onFillExample,
}) {
  return (
    <section className="panel panel--input">
      <div className="panel__header">
        <div>
          <p className="panel__eyebrow">输入区</p>
          <h2 className="panel__title">JD / 简历 / 公司信息</h2>
        </div>
        <button
          type="button"
          className="button button--ghost"
          onClick={onFillExample}
          disabled={loading}
        >
          填充示例
        </button>
      </div>

      <form className="form" onSubmit={onSubmit}>
        <label className="field">
          <span className="field__label">岗位 JD</span>
          <textarea
            className="field__control field__control--textarea"
            value={jd}
            onChange={(e) => onJdChange(e.target.value)}
            rows={9}
            placeholder="粘贴岗位 JD"
          />
        </label>

        <label className="field">
          <span className="field__label">简历</span>
          <textarea
            className="field__control field__control--textarea"
            value={resume}
            onChange={(e) => onResumeChange(e.target.value)}
            rows={9}
            placeholder="粘贴你的简历内容"
          />
        </label>

        <div className="field-grid">
          <label className="field">
            <span className="field__label">公司名</span>
            <input
              className="field__control"
              value={company}
              onChange={(e) => onCompanyChange(e.target.value)}
              placeholder="例如：字节跳动"
            />
          </label>

          <label className="field">
            <span className="field__label">额外要求</span>
            <input
              className="field__control"
              value={extra}
              onChange={(e) => onExtraChange(e.target.value)}
              placeholder="例如：请补充公司背景和岗位画像"
            />
          </label>
        </div>

        <div className="form__actions">
          <button type="submit" className="button button--primary" disabled={loading}>
            {loading ? '执行中…' : '开始分析'}
          </button>
          <div className="form__hint">
            {loading ? '正在通过流式事件显示 Agent 执行过程。' : '提交后会实时展示节点状态与最终报告。'}
          </div>
        </div>

        {error ? <div className="alert alert--error">错误：{error}</div> : null}
      </form>
    </section>
  )
}

export default InputForm
