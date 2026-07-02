import LearningMindMap from '../components/LearningMindMap'
import type { LLMRoleProfileResult } from '../types/api'
import type { MindMapBranch, RoleSummary } from '../types/app'

type LearningMapPageProps = {
  roleSummaries: RoleSummary[]
  selectedRole: RoleSummary | null
  mindMapBranches: MindMapBranch[]
  mindMapZoom: number
  collapsedBranchIds: string[]
  roleProfileResult: LLMRoleProfileResult | null
  generatingRoleProfileName: string | null
  onSelectedRoleChange: (roleName: string) => void
  onGenerateRoleProfile: (roleName: string) => void
  onZoom: (delta: number) => void
  onResetView: () => void
  onExpandAll: () => void
  onToggleBranch: (branchId: string) => void
}

function LearningMapPage(props: LearningMapPageProps) {
  return <LearningMindMap {...props} />
}

export default LearningMapPage
