import type { DragEvent } from 'react'
import JobCardItem from '../components/JobCardItem'
import type { CompanyProfile, JobCard } from '../types/api'
import type { EditableJobField, JobEditDraft } from '../types/app'

type JobCardsPageProps = {
  jobCards: JobCard[]
  companyProfiles: Record<string, CompanyProfile>
  editingJobId: number | null
  editDraft: JobEditDraft | null
  savingJobId: number | null
  deletingJobId: number | null
  reextractingJobId: number | null
  enrichingCompanyName: string | null
  isRebuildingWithLLM: boolean
  draggedJobId: number | null
  dragOverJobId: number | null
  expandedJobId: number | null
  errorMessage: string | null
  onDraftChange: (field: EditableJobField, value: string) => void
  onSaveJob: (jobId: number) => void
  onCancelEditing: () => void
  onStartEditing: (job: JobCard) => void
  onDeleteJob: (job: JobCard) => void
  onReextractJob: (job: JobCard) => void
  onEnrichCompany: (companyName: string) => void
  onRebuildLLMJobs: () => void
  onTogglePinned: (job: JobCard) => void
  onToggleDetails: (jobId: number) => void
  onJobDragStart: (jobId: number, event: DragEvent<HTMLElement>) => void
  onJobDragOver: (jobId: number, event: DragEvent<HTMLElement>) => void
  onJobDrop: (event: DragEvent<HTMLElement>) => void
  onJobDragEnd: () => void
}

function JobCardsPage({
  jobCards,
  companyProfiles,
  editingJobId,
  editDraft,
  savingJobId,
  deletingJobId,
  reextractingJobId,
  enrichingCompanyName,
  isRebuildingWithLLM,
  draggedJobId,
  dragOverJobId,
  expandedJobId,
  errorMessage,
  onDraftChange,
  onSaveJob,
  onCancelEditing,
  onStartEditing,
  onDeleteJob,
  onReextractJob,
  onEnrichCompany,
  onRebuildLLMJobs,
  onTogglePinned,
  onToggleDetails,
  onJobDragStart,
  onJobDragOver,
  onJobDrop,
  onJobDragEnd,
}: JobCardsPageProps) {
  return (
    <section className="records-section" id="jobs">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Job Cards</p>
          <h3>岗位卡片</h3>
        </div>
        {jobCards.length > 0 ? (
          <button
            className="text-action"
            type="button"
            onClick={onRebuildLLMJobs}
            disabled={isRebuildingWithLLM}
          >
            {isRebuildingWithLLM ? 'LLM重抽中' : '全部用LLM重抽'}
          </button>
        ) : null}
      </div>

      {errorMessage ? <p className="form-error">{errorMessage}</p> : null}

      {jobCards.length === 0 ? (
        <div className="empty-state">
          <p>还没有生成岗位卡。粘贴一段岗位文本试试。</p>
        </div>
      ) : (
        <div className="job-card-list">
          {jobCards.map((job) => (
            <JobCardItem
              key={job.id}
              job={job}
              editDraft={editDraft}
              isEditing={editingJobId === job.id}
              isExpanded={expandedJobId === job.id}
              isDragging={draggedJobId === job.id}
              isDragOver={dragOverJobId === job.id}
              savingJobId={savingJobId}
              deletingJobId={deletingJobId}
              reextractingJobId={reextractingJobId}
              companyProfile={
                job.company_name ? companyProfiles[job.company_name] ?? null : null
              }
              enrichingCompanyName={enrichingCompanyName}
              onDraftChange={onDraftChange}
              onSaveJob={onSaveJob}
              onCancelEditing={onCancelEditing}
              onStartEditing={onStartEditing}
              onDeleteJob={onDeleteJob}
              onReextractJob={onReextractJob}
              onEnrichCompany={onEnrichCompany}
              onTogglePinned={onTogglePinned}
              onToggleDetails={onToggleDetails}
              onDragStart={onJobDragStart}
              onDragOver={onJobDragOver}
              onDrop={onJobDrop}
              onDragEnd={onJobDragEnd}
            />
          ))}
        </div>
      )}
    </section>
  )
}

export default JobCardsPage
