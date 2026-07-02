import { useCallback, useRef, useState } from 'react'
import type { CSSProperties, DragEvent } from 'react'
import {
  confidenceLabels,
  salaryPeriodLabels,
} from '../constants/app'
import type { CompanyProfile, JobCard } from '../types/api'
import type { EditableJobField, JobEditDraft } from '../types/app'

type JobCardItemProps = {
  job: JobCard
  editDraft: JobEditDraft | null
  isEditing: boolean
  isExpanded: boolean
  isDragging: boolean
  isDragOver: boolean
  savingJobId: number | null
  deletingJobId: number | null
  reextractingJobId: number | null
  companyProfile: CompanyProfile | null
  enrichingCompanyName: string | null
  onDraftChange: (field: EditableJobField, value: string) => void
  onSaveJob: (jobId: number) => void
  onCancelEditing: () => void
  onStartEditing: (job: JobCard) => void
  onDeleteJob: (job: JobCard) => void
  onReextractJob: (job: JobCard) => void
  onEnrichCompany: (companyName: string) => void
  onTogglePinned: (job: JobCard) => void
  onToggleDetails: (jobId: number) => void
  onDragStart: (jobId: number, event: DragEvent<HTMLElement>) => void
  onDragOver: (jobId: number, event: DragEvent<HTMLElement>) => void
  onDrop: (event: DragEvent<HTMLElement>) => void
  onDragEnd: () => void
}

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
  inference_notes: '推测说明',
}

const sourceLabels: Record<string, string> = {
  original_posting: '原文提取',
  external_search: '外部补全',
  model_inference: '模型推测',
  user_edit: '用户编辑',
  missing: '缺失',
}

function JobCardItem({
  job,
  editDraft,
  isEditing,
  isExpanded,
  isDragging,
  isDragOver,
  savingJobId,
  deletingJobId,
  reextractingJobId,
  companyProfile,
  enrichingCompanyName,
  onDraftChange,
  onSaveJob,
  onCancelEditing,
  onStartEditing,
  onDeleteJob,
  onReextractJob,
  onEnrichCompany,
  onTogglePinned,
  onToggleDetails,
  onDragStart,
  onDragOver,
  onDrop,
  onDragEnd,
}: JobCardItemProps) {
  if (isEditing && editDraft) {
    return (
      <article className="job-card editing">
        <header>
          <div>
            <span className={`confidence-chip ${job.confidence}`}>
              抽取置信度：{confidenceLabels[job.confidence] ?? job.confidence}
            </span>
            <h4>编辑岗位卡</h4>
          </div>
          <div className="card-actions">
            <button type="button" onClick={() => onSaveJob(job.id)}>
              {savingJobId === job.id ? '保存中' : '保存'}
            </button>
            <button className="ghost-action" type="button" onClick={onCancelEditing}>
              取消
            </button>
          </div>
        </header>

        <div className="edit-grid">
          <label>
            <span>岗位名称</span>
            <input
              value={editDraft.title}
              onChange={(event) => onDraftChange('title', event.target.value)}
            />
          </label>
          <label>
            <span>公司</span>
            <input
              value={editDraft.company_name}
              onChange={(event) => onDraftChange('company_name', event.target.value)}
            />
          </label>
          <label>
            <span>岗位大类</span>
            <input
              value={editDraft.role_category}
              onChange={(event) => onDraftChange('role_category', event.target.value)}
            />
          </label>
          <label>
            <span>薪资</span>
            <input
              value={editDraft.salary_range}
              placeholder="10-15K"
              onChange={(event) => onDraftChange('salary_range', event.target.value)}
            />
          </label>
          <label>
            <span>薪资周期</span>
            <select
              value={editDraft.salary_period}
              onChange={(event) => onDraftChange('salary_period', event.target.value)}
            >
              <option value="">待补全</option>
              <option value="monthly">月薪</option>
              <option value="daily">日薪</option>
              <option value="yearly">年薪</option>
            </select>
          </label>
          <label>
            <span>Base</span>
            <input
              value={editDraft.base_location}
              onChange={(event) => onDraftChange('base_location', event.target.value)}
            />
          </label>
          <label>
            <span>学历</span>
            <input
              value={editDraft.education_requirement}
              onChange={(event) =>
                onDraftChange('education_requirement', event.target.value)
              }
            />
          </label>
          <label>
            <span>经验</span>
            <input
              value={editDraft.experience_requirement}
              onChange={(event) =>
                onDraftChange('experience_requirement', event.target.value)
              }
            />
          </label>
        </div>

        <div className="edit-textareas">
          <label>
            <span>技能，一行一个</span>
            <textarea
              value={editDraft.skillsText}
              onChange={(event) => onDraftChange('skillsText', event.target.value)}
            />
          </label>
          <label>
            <span>岗位职责，一行一个</span>
            <textarea
              value={editDraft.responsibilitiesText}
              onChange={(event) =>
                onDraftChange('responsibilitiesText', event.target.value)
              }
            />
          </label>
          <label>
            <span>任职要求，一行一个</span>
            <textarea
              value={editDraft.requirementsText}
              onChange={(event) =>
                onDraftChange('requirementsText', event.target.value)
              }
            />
          </label>
          <label>
            <span>加分项，一行一个</span>
            <textarea
              value={editDraft.bonusPointsText}
              onChange={(event) =>
                onDraftChange('bonusPointsText', event.target.value)
              }
            />
          </label>
        </div>
      </article>
    )
  }

  const fieldSourceRows = Object.entries(job.field_sources).filter(
    ([fieldName, source]) => source || job.evidence[fieldName],
  )
  const inferredFields = fieldSourceRows
    .filter(([, source]) => source === 'model_inference')
    .map(([fieldName]) => fieldLabels[fieldName] ?? fieldName)
  const fieldValueMap = buildFieldValueMap(job)

  return (
    <article
      className={`job-card ${isExpanded ? 'expanded' : ''} ${
        job.is_pinned ? 'pinned' : ''
      } ${
        isDragging ? 'dragging' : ''
      } ${isDragOver ? 'drag-over' : ''}`}
      draggable
      onDragStart={(event) => onDragStart(job.id, event)}
      onDragOver={(event) => onDragOver(job.id, event)}
      onDrop={onDrop}
      onDragEnd={onDragEnd}
    >
      <div
        className={`job-card-summary ${isExpanded ? 'expanded' : ''}`}
        onClick={() => {
          if (!isExpanded) {
            onToggleDetails(job.id)
          }
        }}
      >
        <header>
          <div>
            <div className="job-card-badges">
              {job.is_pinned ? <span className="pin-chip">置顶</span> : null}
              <span className={`confidence-chip ${job.confidence}`}>
                抽取置信度：{confidenceLabels[job.confidence] ?? job.confidence}
              </span>
            </div>
            <h4>{job.title}</h4>
          </div>
          <div className="card-actions" onClick={(event) => event.stopPropagation()}>
            <button
              type="button"
              aria-expanded={isExpanded}
              onClick={() => onToggleDetails(job.id)}
            >
              {isExpanded ? '收起详情' : '展开详情'}
            </button>
            <button type="button" onClick={() => onTogglePinned(job)}>
              {job.is_pinned ? '取消置顶' : '置顶'}
            </button>
            <button type="button" onClick={() => onStartEditing(job)}>
              编辑
            </button>
            <button
              type="button"
              onClick={() => onReextractJob(job)}
              disabled={reextractingJobId === job.id}
            >
              {reextractingJobId === job.id ? '抽取中' : 'LLM重抽'}
            </button>
            <button
              className="danger-action"
              type="button"
              onClick={() => onDeleteJob(job)}
              disabled={deletingJobId === job.id}
            >
              {deletingJobId === job.id ? '删除中' : '删除'}
            </button>
          </div>
        </header>

        <div className="job-meta">
          {job.company_name ? (
            <CompanyMetaChip
              job={job}
              companyProfile={companyProfile}
              enrichingCompanyName={enrichingCompanyName}
              onEnrichCompany={onEnrichCompany}
            />
          ) : null}
          {job.role_category ? <span>{job.role_category}</span> : null}
          {job.salary_range ? (
            <span>
              {`${job.salary_range} · ${
                salaryPeriodLabels[job.salary_period ?? ''] ?? '薪资周期待确认'
              }`}
            </span>
          ) : null}
          {job.base_location ? <span>{`Base：${job.base_location}`}</span> : null}
          {job.education_requirement ? <span>{job.education_requirement}</span> : null}
          {job.experience_requirement ? <span>{job.experience_requirement}</span> : null}
        </div>

        {job.skills.length > 0 ? (
          <div className="skill-list compact">
            {job.skills.slice(0, 10).map((skill) => (
              <span key={skill}>{skill}</span>
            ))}
            {job.skills.length > 10 ? <span>+{job.skills.length - 10}</span> : null}
          </div>
        ) : null}

        <div className={`job-preview-grid ${isExpanded ? 'expanded' : ''}`}>
          <InfoBlock
            title="岗位职责"
            items={job.responsibilities}
            isExpanded={isExpanded}
          />
          <InfoBlock
            title="任职要求"
            items={job.requirements}
            isExpanded={isExpanded}
          />
          <InfoBlock
            title="加分项"
            items={job.bonus_points}
            isExpanded={isExpanded}
            source={job.field_sources.bonus_points}
            emptyText="暂无加分项"
          />
        </div>
      </div>

      {isExpanded ? (
        <div className="job-detail-panel">
          <section className="detail-section">
            <h5>技能与工具</h5>
            {job.skills.length > 0 ? (
              <div className="skill-list">
                {job.skills.map((skill) => (
                  <span key={skill}>{skill}</span>
                ))}
              </div>
            ) : (
              <p>暂无技能标签</p>
            )}
          </section>

          <details className="detail-section source-section source-disclosure">
            <summary>字段来源与证据</summary>
            {fieldSourceRows.length > 0 ? (
              <div className="source-evidence-grid">
                {fieldSourceRows.map(([fieldName, source]) => (
                  <div className="source-evidence-row" key={fieldName}>
                    <strong>{fieldLabels[fieldName] ?? fieldName}</strong>
                    <span className={`source-marker ${source}`}>
                      {sourceLabels[source] ?? source}
                    </span>
                    <p>
                      {formatEvidenceText(
                        job.evidence[fieldName],
                        source,
                        fieldValueMap[fieldName],
                      )}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p>暂无字段来源记录。</p>
            )}

            {inferredFields.length > 0 ? (
              <p className="inference-note">
                模型推测字段：{inferredFields.join('、')}
              </p>
            ) : null}
          </details>
        </div>
      ) : null}
    </article>
  )
}

function CompanyMetaChip({
  job,
  companyProfile,
  enrichingCompanyName,
  onEnrichCompany,
}: {
  job: JobCard
  companyProfile: CompanyProfile | null
  enrichingCompanyName: string | null
  onEnrichCompany: (companyName: string) => void
}) {
  const companyName = job.company_name || '公司待补全'
  const isEnriching = enrichingCompanyName === companyName
  const hasCompanyName = Boolean(job.company_name)
  const hasProfileFacts = companyProfile ? hasUsefulCompanyProfile(companyProfile) : false
  const hasDisplayableFacts = companyProfile
    ? hasDisplayableCompanyFacts(companyProfile)
    : false
  const chipRef = useRef<HTMLSpanElement | null>(null)
  const [popoverStyle, setPopoverStyle] = useState<CSSProperties>({})

  const updatePopoverPosition = useCallback(() => {
    const rect = chipRef.current?.getBoundingClientRect()
    if (!rect) {
      return
    }

    const margin = 16
    const gap = 10
    const availableWidth = Math.max(180, window.innerWidth - margin * 2)
    const width = Math.min(360, availableWidth)
    const minLeft = margin
    const maxLeft = Math.max(minLeft, window.innerWidth - width - margin)
    const left = Math.min(Math.max(rect.left, minLeft), maxLeft)
    const spaceBelow = window.innerHeight - rect.bottom - gap - margin
    const spaceAbove = rect.top - gap - margin
    const opensUp = spaceBelow < 220 && spaceAbove > spaceBelow
    const availableHeight = Math.max(140, opensUp ? spaceAbove : spaceBelow)
    const maxHeight = Math.min(
      Math.max(140, window.innerHeight - margin * 2),
      availableHeight,
    )
    const top = opensUp ? rect.top - gap : rect.bottom + gap

    setPopoverStyle({
      '--company-popover-left': `${left}px`,
      '--company-popover-top': `${top}px`,
      '--company-popover-width': `${width}px`,
      '--company-popover-max-height': `${maxHeight}px`,
      '--company-popover-hidden-transform': opensUp
        ? 'translateY(calc(-100% + 4px))'
        : 'translateY(-4px)',
      '--company-popover-visible-transform': opensUp
        ? 'translateY(-100%)'
        : 'translateY(0)',
    } as CSSProperties)
  }, [])

  return (
    <span
      ref={chipRef}
      className="company-meta-chip"
      tabIndex={0}
      onMouseEnter={updatePopoverPosition}
      onFocus={updatePopoverPosition}
      onClick={(event) => event.stopPropagation()}
      onKeyDown={(event) => event.stopPropagation()}
    >
      {companyName}
      <span className="company-popover" role="tooltip" style={popoverStyle}>
        <strong>{companyName}</strong>
        {companyProfile && hasProfileFacts ? (
          <>
            {hasDisplayableFacts ? (
              <dl>
                <CompanyFact label="行业" value={companyProfile.industry} />
                <CompanyFact label="融资" value={companyProfile.financing_stage} />
                <CompanyFact label="规模" value={companyProfile.scale} />
                <CompanyFact label="总部" value={companyProfile.headquarters} />
                <CompanyLink label="官网" value={companyProfile.official_website} />
                <CompanyLink
                  label="招聘页"
                  value={companyProfile.official_careers_url}
                />
              </dl>
            ) : null}
            {companyProfile.summary ? <p>{companyProfile.summary}</p> : null}
            {companyProfile.source_urls.length > 0 ? (
              <small>来源：{companyProfile.source_urls.slice(0, 2).join(' / ')}</small>
            ) : (
              <small>
                暂无可靠来源链接；普通模型 API 不会自动联网搜索，当前结果请按字段来源判断可信度。
              </small>
            )}
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                if (job.company_name) {
                  onEnrichCompany(job.company_name)
                }
              }}
              disabled={!hasCompanyName || isEnriching}
            >
              {isEnriching ? '补全中' : '重新联网补全'}
            </button>
          </>
        ) : (
          <>
            <p>
              {companyProfile
                ? '公司画像已查过，但当前没有可靠公司事实。配置检索 API 后可以重新联网补全；没有检索结果时会退回普通 LLM。'
                : '公司画像还未补全。点击下方按钮会优先调用当前检索 API，再交给 LLM 结构化并保存到本地库。'}
            </p>
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation()
                if (job.company_name) {
                  onEnrichCompany(job.company_name)
                }
              }}
              disabled={!hasCompanyName || isEnriching}
            >
              {isEnriching ? '补全中' : '联网补全公司'}
            </button>
          </>
        )}
      </span>
    </span>
  )
}

function hasUsefulCompanyProfile(profile: CompanyProfile) {
  return Boolean(
    profile.summary ||
      hasDisplayableCompanyFacts(profile) ||
      profile.source_urls.length > 0,
  )
}

function hasDisplayableCompanyFacts(profile: CompanyProfile) {
  return Boolean(
    profile.industry ||
      profile.financing_stage ||
      profile.scale ||
      profile.headquarters ||
      profile.official_website ||
      profile.official_careers_url,
  )
}

function CompanyFact({ label, value }: { label: string; value: string | null }) {
  if (!value) {
    return null
  }

  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  )
}

function CompanyLink({ label, value }: { label: string; value: string | null }) {
  if (!value) {
    return null
  }

  return (
    <div>
      <dt>{label}</dt>
      <dd>
        <a href={value} target="_blank" rel="noreferrer">
          {value}
        </a>
      </dd>
    </div>
  )
}

function buildFieldValueMap(job: JobCard): Record<string, string> {
  return {
    title: job.title,
    company_name: job.company_name ?? '',
    role_category: job.role_category ?? '',
    salary_range: job.salary_range ?? '',
    salary_period: salaryPeriodLabels[job.salary_period ?? ''] ?? job.salary_period ?? '',
    base_location: job.base_location ?? '',
    education_requirement: job.education_requirement ?? '',
    experience_requirement: job.experience_requirement ?? '',
    responsibilities: job.responsibilities.join(' / '),
    requirements: job.requirements.join(' / '),
    bonus_points: job.bonus_points.join(' / '),
    skills: job.skills.join(' / '),
  }
}

function formatEvidenceText(
  evidence: string | null | undefined,
  source: string,
  fieldValue: string | undefined,
) {
  if (evidence) {
    return fieldValue && evidence !== fieldValue
      ? `字段值：${fieldValue}；证据：${evidence}`
      : evidence
  }
  if (source === 'original_posting') {
    return fieldValue
      ? `证据片段待补：该字段标为原文提取，字段值为“${fieldValue}”。`
      : '证据片段待补：该字段标为原文提取，但旧抽取结果未保存原文片段。'
  }
  if (source === 'model_inference') {
    return '模型推测，无直接原文证据。'
  }
  if (source === 'missing') {
    return '原文未提供该字段。'
  }
  return '暂无证据记录。'
}

function InfoBlock({
  title,
  items,
  isExpanded,
  source,
  emptyText = '待补全',
}: {
  title: string
  items: string[]
  isExpanded: boolean
  source?: string
  emptyText?: string
}) {
  const isInferred = source === 'model_inference'
  return (
    <section className={`job-info-block ${isExpanded ? 'expanded' : ''}`}>
      <div className="info-block-heading">
        <h5>{title}</h5>
        {isInferred ? <span>模型推测</span> : null}
      </div>
      {items.length > 0 ? (
        isExpanded ? (
          <ul>
            {items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        ) : (
          <p>{items.slice(0, 2).join(' / ')}</p>
        )
      ) : (
        <p>{emptyText}</p>
      )}
    </section>
  )
}

export default JobCardItem
