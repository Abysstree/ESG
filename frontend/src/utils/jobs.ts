import type { JobCard } from '../types/api'
import type { JobEditDraft } from '../types/app'

export function toEditDraft(job: JobCard): JobEditDraft {
  return {
    title: job.title,
    company_name: job.company_name ?? '',
    role_category: job.role_category ?? '',
    salary_range: job.salary_range ?? '',
    salary_period: job.salary_period ?? '',
    base_location: job.base_location ?? '',
    education_requirement: job.education_requirement ?? '',
    experience_requirement: job.experience_requirement ?? '',
    skillsText: job.skills.join('\n'),
    responsibilitiesText: job.responsibilities.join('\n'),
    requirementsText: job.requirements.join('\n'),
    bonusPointsText: job.bonus_points.join('\n'),
  }
}

export function splitLines(value: string): string[] {
  return value
    .split('\n')
    .map((item) => item.trim())
    .filter(Boolean)
}

export function sortJobCards(cards: JobCard[]): JobCard[] {
  return [...cards].sort((first, second) => {
    if (first.is_pinned !== second.is_pinned) {
      return first.is_pinned ? -1 : 1
    }
    if (first.sort_order !== second.sort_order) {
      return first.sort_order - second.sort_order
    }
    return new Date(second.created_at).getTime() - new Date(first.created_at).getTime()
  })
}

export function moveJobCard(cards: JobCard[], draggedId: number, targetId: number): JobCard[] {
  const nextCards = [...cards]
  const draggedIndex = nextCards.findIndex((job) => job.id === draggedId)
  const targetIndex = nextCards.findIndex((job) => job.id === targetId)

  if (draggedIndex < 0 || targetIndex < 0 || draggedIndex === targetIndex) {
    return cards
  }

  const [draggedJob] = nextCards.splice(draggedIndex, 1)
  nextCards.splice(targetIndex, 0, draggedJob)
  return nextCards
}
