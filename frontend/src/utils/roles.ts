import type { JobCard, LLMRoleProfile } from '../types/api'
import type { MindMapBranch, MindMapNode, RoleSummary } from '../types/app'

export function deriveRoleSummaries(cards: JobCard[]): RoleSummary[] {
  const groupedCards = new Map<string, JobCard[]>()
  for (const card of cards) {
    const roleName = card.role_category?.trim() || '待分类岗位'
    groupedCards.set(roleName, [...(groupedCards.get(roleName) ?? []), card])
  }

  return Array.from(groupedCards.entries())
    .map(([name, roleCards]) => ({
      name,
      jobCount: roleCards.length,
      titles: uniqueValues(roleCards.map((card) => card.title), 5),
      companies: uniqueValues(
        roleCards.map((card) => card.company_name).filter(Boolean) as string[],
        5,
      ),
      baseLocations: uniqueValues(
        roleCards.map((card) => card.base_location).filter(Boolean) as string[],
        5,
      ),
      salarySamples: uniqueValues(
        roleCards.map((card) => card.salary_range).filter(Boolean) as string[],
        4,
      ),
      educationRequirements: topValues(
        roleCards.map((card) => card.education_requirement).filter(Boolean) as string[],
        4,
      ),
      experienceRequirements: topValues(
        roleCards.map((card) => card.experience_requirement).filter(Boolean) as string[],
        4,
      ),
      topSkills: topValues(
        roleCards.flatMap((card) => card.skills),
        14,
      ),
      commonResponsibilities: topValues(
        roleCards.flatMap((card) => card.responsibilities),
        6,
      ),
      commonRequirements: topValues(
        roleCards.flatMap((card) => card.requirements),
        7,
      ),
      commonBonusPoints: topValues(
        roleCards.flatMap((card) => card.bonus_points),
        5,
      ),
    }))
    .sort(
      (first, second) =>
        second.jobCount - first.jobCount || first.name.localeCompare(second.name),
    )
}

function uniqueValues(values: string[], limit: number): string[] {
  const seen = new Set<string>()
  const result = []
  for (const value of values) {
    const cleaned = value.trim()
    if (!cleaned || seen.has(cleaned)) continue
    seen.add(cleaned)
    result.push(cleaned)
    if (result.length >= limit) break
  }
  return result
}

function topValues(values: string[], limit: number): string[] {
  const counts = new Map<string, number>()
  for (const value of values) {
    const cleaned = value.trim()
    if (!cleaned) continue
    counts.set(cleaned, (counts.get(cleaned) ?? 0) + 1)
  }

  return Array.from(counts.entries())
    .sort(([firstValue, firstCount], [secondValue, secondCount]) => {
      if (firstCount !== secondCount) return secondCount - firstCount
      return firstValue.localeCompare(secondValue)
    })
    .slice(0, limit)
    .map(([value]) => value)
}

export function buildMindMapBranches(role: RoleSummary): MindMapBranch[] {
  return [
    createMindMapBranch('core-skills', '核心技能', 'left', 110, 90, '#6d6259', role.topSkills.slice(0, 8)),
    createMindMapBranch(
      'engineering-tools',
      '工程工具',
      'right',
      800,
      315,
      '#7654c4',
      pickMatchingItems(
        role.topSkills,
        [
          'Python',
          'C++',
          'C语言',
          'Linux',
          'Docker',
          'Git',
          'VTK',
          'ITK',
          'Open3D',
          'PyVista',
          'ROS',
          'CUDA',
          'Matlab',
          'OpenCV',
        ],
        role.topSkills.slice(0, 6),
      ),
    ),
    createMindMapBranch(
      'algorithm-methods',
      '算法方法',
      'left',
      80,
      330,
      '#706572',
      pickMatchingItems(
        [...role.topSkills, ...role.commonRequirements],
        [
          '深度学习',
          '机器学习',
          '配准',
          '分割',
          'SLAM',
          'ICP',
          'B-spline',
          'Demons',
          '光流',
          '三维重建',
          '目标检测',
          '图像处理',
        ],
        role.commonRequirements.slice(0, 6),
      ),
    ),
    createMindMapBranch(
      'domain-knowledge',
      '领域知识',
      'right',
      820,
      80,
      '#19bca9',
      pickMatchingItems(
        [...role.topSkills, ...role.commonRequirements],
        ['医学影像', '自动驾驶', '光学', '嵌入式', 'CT', 'MRI', '传感器融合', '点云', 'mesh', 'STL'],
        role.topSkills.slice(0, 6),
      ),
    ),
    createMindMapBranch(
      'project-practice',
      '项目实践',
      'right',
      790,
      575,
      '#9bd94e',
      role.commonResponsibilities.slice(0, 7),
    ),
    createMindMapBranch(
      'quality-research',
      '质控研究',
      'left',
      105,
      620,
      '#0b58b4',
      pickMatchingItems(
        [...role.commonRequirements, ...role.commonBonusPoints],
        ['论文', '复现', '失败', '异常', '质量', '稳定', '合理', '可解释', '统计'],
        [...role.commonBonusPoints, ...role.commonRequirements].slice(0, 6),
      ),
    ),
    createMindMapBranch(
      'interview-portfolio',
      '面试作品',
      'left',
      190,
      800,
      '#0b6425',
      [
        ...role.commonBonusPoints.slice(0, 4),
        ...role.titles.map((title) => `${title} 作品集`),
      ],
    ),
  ]
}

export function buildMindMapBranchesFromLLMProfile(
  profile: LLMRoleProfile | null | undefined,
): MindMapBranch[] {
  const branches = profile?.learning_map?.branches ?? []
  if (!branches.length) return []

  const positions = [
    { side: 'left' as const, x: 110, y: 90, color: '#6d6259' },
    { side: 'right' as const, x: 820, y: 80, color: '#19bca9' },
    { side: 'left' as const, x: 80, y: 330, color: '#706572' },
    { side: 'right' as const, x: 800, y: 315, color: '#7654c4' },
    { side: 'right' as const, x: 790, y: 575, color: '#9bd94e' },
    { side: 'left' as const, x: 105, y: 620, color: '#0b58b4' },
    { side: 'left' as const, x: 190, y: 800, color: '#0b6425' },
  ]

  return branches.slice(0, positions.length).map((branch, index) => {
    const position = positions[index]
    return createMindMapBranch(
      branch.id || `llm-branch-${index}`,
      branch.title || branch.focus || `分支 ${index + 1}`,
      position.side,
      position.x,
      position.y,
      position.color,
      branch.nodes.map((node, nodeIndex) => convertLLMNode(node, `${branch.id}-${nodeIndex}`)),
      {
        focus: branch.focus,
        sourceFields: branch.source_fields,
        evidence: branch.evidence,
      },
    )
  })
}

function convertLLMNode(
  node: LLMRoleProfile['learning_map']['branches'][number]['nodes'][number],
  fallbackId: string,
): MindMapNode {
  const nodeId = normalizeMindMapId(node.id || fallbackId)
  return {
    id: nodeId,
    title: normalizeMindMapItem(node.title),
    nodeType: node.node_type || 'learning_point',
    level: node.level || 'foundation',
    sourceFields: node.source_fields ?? [],
    evidence: node.evidence ?? [],
    children: (node.children ?? []).map((child, index) =>
      convertLLMNode(child, `${nodeId}-${index}`),
    ),
  }
}

function createMindMapBranch(
  id: string,
  title: string,
  side: 'left' | 'right',
  x: number,
  y: number,
  color: string,
  itemsOrNodes: string[] | MindMapNode[],
  options: {
    focus?: string
    sourceFields?: string[]
    evidence?: string[]
  } = {},
): MindMapBranch {
  const nodes = toMindMapNodes(itemsOrNodes)
  return {
    id,
    title,
    side,
    x,
    y,
    color,
    items: nodes.map((node) => node.title),
    nodes,
    sourceFields: options.sourceFields ?? [],
    evidence: options.evidence ?? [],
    focus: options.focus ?? title,
  }
}

function toMindMapNodes(itemsOrNodes: string[] | MindMapNode[]): MindMapNode[] {
  if (itemsOrNodes.length > 0 && typeof itemsOrNodes[0] !== 'string') {
    return (itemsOrNodes as MindMapNode[]).filter((node) => node.title)
  }

  return compactMindMapItems(itemsOrNodes as string[]).map((item, index) => ({
    id: normalizeMindMapId(`${index}-${item}`),
    title: item,
    nodeType: 'learning_point',
    level: 'foundation',
    sourceFields: [],
    evidence: [item],
    children: [],
  }))
}

function compactMindMapItems(items: string[]): string[] {
  const compactedItems = uniqueValues(items.map(normalizeMindMapItem), 5)
  return compactedItems.length ? compactedItems : ['待更多岗位样本补全']
}

function normalizeMindMapItem(item: string): string {
  return item.replace(/\s+/g, ' ').trim()
}

function normalizeMindMapId(value: string): string {
  return value
    .replace(/\s+/g, '-')
    .replace(/[^\w.\-\u4e00-\u9fa5]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    || 'node'
}

function pickMatchingItems(items: string[], keywords: string[], fallback: string[]): string[] {
  const matchedItems = items.filter((item) =>
    keywords.some((keyword) => item.toLowerCase().includes(keyword.toLowerCase())),
  )
  return uniqueValues(matchedItems.length ? matchedItems : fallback, 5)
}
