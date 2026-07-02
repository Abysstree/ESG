import type { FormEvent } from 'react'
import { confidenceLabels, providerTypeLabels } from '../constants/app'
import type { LLMExtractPreview, LLMExtractedJobCard, LLMStatus } from '../types/api'

type ExtractionDebugPageProps = {
  rawText: string
  result: LLMExtractPreview | null
  llmStatus: LLMStatus | null
  isRunning: boolean
  errorMessage: string | null
  onRawTextChange: (value: string) => void
  onRun: () => void
}

const sampleJobText = `医学影像处理算法工程师
芯动云图 未融资
南京·1-3年·硕士
10-15K

岗位职责
1.负责三维及动态医学影像数据的处理、分析和算法开发；
2.参与 CT、CTA、MRI 等医学影像的多相位数据整理、配准和时序一致性分析；
3.负责刚性配准、非刚性配准、位移场、形变场、中心线、截面分析等算法实现；

任职要求
1.硕士及以上学历，计算机、图形学、人工智能、生物医学工程、医学影像等相关专业；
2.必须有三维医学影像、点云、mesh、STL、VTK、Open3D 等至少一种三维数据处理经验；
3.必须具备 Python 或 Rust 或 C++ 编程能力；

加分项
1.做过 4D-CT/4D-CTA、心脏 CT、cine MRI、PC-MRI 等动态医学影像；
2.熟悉 VTK、ITK、SimpleITK、Open3D、PyVista、CGAL、scikit-image；

所在公司
南京芯动云图技术有限公司`

const fieldLabels: Record<string, string> = {
  title: '岗位名称',
  company_name: '公司',
  role_category: '岗位大类',
  salary_range: '薪资',
  salary_period: '薪资周期',
  base_location: 'Base',
  education_requirement: '学历',
  experience_requirement: '经验',
  responsibilities: '岗位职责',
  requirements: '任职要求',
  bonus_points: '加分项',
  skills: '技能',
}

const sourceLabels: Record<string, string> = {
  original_posting: '原文提取',
  external_search: '外部补全',
  model_inference: '模型推测',
  user_edit: '用户编辑',
  missing: '缺失',
}

function ExtractionDebugPage({
  rawText,
  result,
  llmStatus,
  isRunning,
  errorMessage,
  onRawTextChange,
  onRun,
}: ExtractionDebugPageProps) {
  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    onRun()
  }

  const extractedJob =
    result?.extracted_schema ?? result?.job_card ?? result?.normalized_job_card ?? null
  const normalizedJob = result?.normalized_job_card ?? extractedJob
  const qualityChecks =
    result?.quality_checks ?? (extractedJob ? buildFallbackQualityChecks(extractedJob) : null)
  const fieldSourceRows = extractedJob ? Object.entries(extractedJob.field_sources) : []

  return (
    <section className="records-section extraction-debug" id="debug">
      <div className="section-heading">
        <p className="eyebrow">Extraction Debug</p>
        <h3>LLM 抽取调试</h3>
      </div>

      <div className="debug-layout">
        <form className="debug-input-panel" onSubmit={handleSubmit}>
          <label className="field debug-textarea-field">
            <span>岗位原文</span>
            <textarea
              value={rawText}
              placeholder="粘贴一段岗位正文，运行后查看模型如何抽取字段、证据和推测。"
              onChange={(event) => onRawTextChange(event.target.value)}
            />
          </label>

          {errorMessage ? <p className="form-error">{errorMessage}</p> : null}

          <div className="debug-actions">
            <button className="primary-action" type="submit" disabled={isRunning}>
              {isRunning ? '抽取中' : '运行抽取'}
            </button>
            <button
              className="secondary-inline-action"
              type="button"
              onClick={() => onRawTextChange(sampleJobText)}
            >
              填入示例
            </button>
            <button
              className="secondary-inline-action"
              type="button"
              onClick={() => onRawTextChange('')}
            >
              清空
            </button>
          </div>
        </form>

        <aside className="debug-model-panel">
          <div>
            <span>当前提供商</span>
            <strong>{formatProviderName(llmStatus?.provider)}</strong>
          </div>
          <div>
            <span>模型</span>
            <strong>{llmStatus?.model || '未配置'}</strong>
          </div>
          <div>
            <span>API 状态</span>
            <strong>{llmStatus?.configured ? '已配置' : '未配置 Key'}</strong>
          </div>
          <div>
            <span>调试结果</span>
            <strong>{result ? `${result.provider} · ${result.mode}` : '待运行'}</strong>
          </div>
        </aside>
      </div>

      {result && normalizedJob ? (
        <div className="debug-results">
          <section className="debug-summary">
            <div>
              <span className={`confidence-chip ${normalizedJob.confidence}`}>
                置信度：
                {confidenceLabels[normalizedJob.confidence] ?? normalizedJob.confidence}
              </span>
              <h4>{normalizedJob.title}</h4>
              <p>
                {normalizedJob.company_name || '公司待补全'} ·{' '}
                {normalizedJob.role_category || '待分类岗位'}
              </p>
            </div>

            <div className="debug-metrics">
              <Metric
                label="字段覆盖"
                value={
                  qualityChecks
                    ? `${qualityChecks.field_source_coverage}/${qualityChecks.required_field_count}`
                    : '待计算'
                }
              />
              <Metric
                label="原文字段"
                value={String(qualityChecks?.original_posting_fields.length ?? 0)}
              />
              <Metric
                label="推测字段"
                value={String(qualityChecks?.inferred_fields.length ?? 0)}
              />
              <Metric
                label="缺失字段"
                value={String(qualityChecks?.missing_fields.length ?? 0)}
              />
            </div>
          </section>

          <div className="debug-card-grid">
            <DebugList title="岗位职责" items={normalizedJob.responsibilities} />
            <DebugList title="任职要求" items={normalizedJob.requirements} />
            <DebugList title="加分项" items={normalizedJob.bonus_points} />
            <DebugList title="技能标签" items={normalizedJob.skills} />
          </div>

          <section className="debug-source-panel">
            <h4>字段来源与证据</h4>
            <div className="source-evidence-grid">
              {fieldSourceRows.map(([fieldName, source]) => (
                <div className="source-evidence-row" key={fieldName}>
                  <strong>{fieldLabels[fieldName] ?? fieldName}</strong>
                  <span className={`source-marker ${source}`}>
                    {sourceLabels[source] ?? source}
                  </span>
                  <p>{normalizedJob.evidence[fieldName] || '暂无直接证据'}</p>
                </div>
              ))}
            </div>
          </section>

          {normalizedJob.inference_notes.length > 0 ? (
            <section className="debug-source-panel">
              <h4>模型推测说明</h4>
              <ul>
                {normalizedJob.inference_notes.map((note) => (
                  <li key={note}>{note}</li>
                ))}
              </ul>
            </section>
          ) : null}

          <div className="debug-json-grid">
            <DebugJson title="模型抽取 JSON" value={extractedJob} />
            <DebugJson title="归一化 JobCard" value={normalizedJob} />
            <DebugJson title="实际 Prompt" value={result.prompt ?? '当前后端响应未包含 prompt，请重启后端后再试。'} />
            <DebugJson
              title="Provider 原始响应"
              value={result.raw_model_response ?? result.raw_response ?? result.provider_result}
            />
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <p>运行一次抽取后，这里会显示字段、证据、推测和原始 JSON。</p>
        </div>
      )}
    </section>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function DebugList({ title, items }: { title: string; items: string[] }) {
  return (
    <section>
      <h4>{title}</h4>
      {items.length > 0 ? (
        <ul>
          {items.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : (
        <p>暂无内容</p>
      )}
    </section>
  )
}

function DebugJson({ title, value }: { title: string; value: unknown }) {
  return (
    <details>
      <summary>{title}</summary>
      <pre>{typeof value === 'string' ? value : JSON.stringify(value, null, 2)}</pre>
    </details>
  )
}

function buildFallbackQualityChecks(jobCard: LLMExtractedJobCard) {
  const requiredFields = [
    'title',
    'company_name',
    'role_category',
    'salary_range',
    'salary_period',
    'base_location',
    'education_requirement',
    'experience_requirement',
    'responsibilities',
    'requirements',
    'bonus_points',
    'skills',
  ]
  const entries = Object.entries(jobCard.field_sources)
  return {
    missing_fields: requiredFields.filter(
      (fieldName) =>
        jobCard.field_sources[fieldName] === 'missing' ||
        isEmptyField(jobCard[fieldName as keyof LLMExtractedJobCard]),
    ),
    inferred_fields: entries
      .filter(([, source]) => source === 'model_inference')
      .map(([fieldName]) => fieldName),
    original_posting_fields: entries
      .filter(([, source]) => source === 'original_posting')
      .map(([fieldName]) => fieldName),
    evidence_fields: Object.entries(jobCard.evidence)
      .filter(([, evidence]) => Boolean(evidence))
      .map(([fieldName]) => fieldName),
    field_source_coverage: requiredFields.filter(
      (fieldName) => fieldName in jobCard.field_sources,
    ).length,
    required_field_count: requiredFields.length,
    confidence: jobCard.confidence,
  }
}

function isEmptyField(value: unknown) {
  return value === null || value === undefined || value === '' || (Array.isArray(value) && value.length === 0)
}

function formatProviderName(providerType: string | null | undefined) {
  if (!providerType) return '检查中'
  return providerTypeLabels[providerType as keyof typeof providerTypeLabels] ?? providerType
}

export default ExtractionDebugPage
