import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties } from 'react'
import {
  Background,
  Controls,
  Handle,
  MiniMap,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  type Edge,
  type Node,
  type NodeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { MIND_MAP_DEFAULT_ZOOM } from '../constants/app'
import type { LLMRoleProfileResult } from '../types/api'
import type { MindMapBranch, RoleSummary } from '../types/app'

type LearningMindMapProps = {
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

type LearningNodeKind = 'center' | 'branch' | 'topic'
type BranchSide = 'left' | 'right'

type LearningNodeData = {
  nodeId: string
  title: string
  subtitle?: string
  kind: LearningNodeKind
  color: string
  side?: BranchSide
  branchId?: string
  branchTitle?: string
  sourceLabel: string
  evidence: string[]
  isCollapsed?: boolean
  isSelected?: boolean
  isExpanded?: boolean
  childCount?: number
}

type LearningGraph = {
  nodes: Node<LearningNodeData>[]
  edges: Edge[]
}

const nodeTypes = {
  learningNode: LearningNode,
}

const BRANCH_NODE_HEIGHT = 116
const BRANCH_LANE_GAP = 96
const COLLAPSED_BRANCH_LANE_HEIGHT = 160
const MIN_EXPANDED_BRANCH_LANE_HEIGHT = 250
const MIN_TOPIC_NODE_HEIGHT = 72
const MIN_EXPANDED_TOPIC_NODE_HEIGHT = 190
const TOPIC_ROW_GAP = 18
const BRANCH_X = 430
const TOPIC_X = 800
const LEFT_TOPIC_SELECTED_EXTRA_WIDTH = 130

function LearningMindMap(props: LearningMindMapProps) {
  return (
    <ReactFlowProvider>
      <LearningMindMapInner {...props} />
    </ReactFlowProvider>
  )
}

function LearningMindMapInner({
  roleSummaries,
  selectedRole,
  mindMapBranches,
  mindMapZoom,
  collapsedBranchIds,
  roleProfileResult,
  generatingRoleProfileName,
  onSelectedRoleChange,
  onGenerateRoleProfile,
  onZoom,
  onResetView,
  onExpandAll,
  onToggleBranch,
}: LearningMindMapProps) {
  const { getNode, getViewport, setCenter, setViewport } = useReactFlow()
  const clickTimerRef = useRef<number | null>(null)
  const [selectedNodeId, setSelectedNodeId] = useState<string>('center')
  const [expandedTopicIds, setExpandedTopicIds] = useState<string[]>([])
  const allTopicNodeIds = useMemo(
    () => buildAllTopicNodeIds(mindMapBranches),
    [mindMapBranches],
  )
  const focusNode = useCallback(
    (nodeId: string, data: LearningNodeData) => {
      const node = getNode(nodeId)
      if (!node) return

      const zoom = data.kind === 'center' ? 0.68 : data.kind === 'branch' ? 0.86 : 1.08
      const branchOffset =
        data.kind === 'branch' ? (data.side === 'left' ? -180 : 180) : 0
      const topicOffset =
        data.kind === 'topic' ? (data.side === 'left' ? -80 : 80) : 0
      const centerX =
        node.position.x + (data.kind === 'center' ? 140 : 150) + branchOffset + topicOffset
      const centerY = node.position.y + (data.kind === 'center' ? 62 : 44)
      void setCenter(centerX, centerY, { zoom, duration: 260 })
    },
    [getNode, setCenter],
  )
  const handleToggleBranch = useCallback(
    (branchId: string) => {
      const willCollapse = !collapsedBranchIds.includes(branchId)
      if (willCollapse) {
        setExpandedTopicIds((currentIds) =>
          currentIds.filter((topicId) => !topicId.startsWith(`topic-${branchId}-`)),
        )
      }
      onToggleBranch(branchId)
    },
    [collapsedBranchIds, onToggleBranch],
  )
  const expandTopic = useCallback((topicId: string) => {
    setExpandedTopicIds((currentIds) =>
      currentIds.includes(topicId)
        ? currentIds
        : [...currentIds, topicId],
    )
  }, [])
  const collapseTopic = useCallback((topicId: string) => {
    setExpandedTopicIds((currentIds) =>
      currentIds.filter((currentId) => currentId !== topicId),
    )
  }, [])
  const clearNodeClickTimer = useCallback(() => {
    if (clickTimerRef.current === null) return
    window.clearTimeout(clickTimerRef.current)
    clickTimerRef.current = null
  }, [])
  const expandWholeMap = useCallback(() => {
    onExpandAll()
    setExpandedTopicIds(allTopicNodeIds)
  }, [allTopicNodeIds, onExpandAll])
  const resetWholeMap = useCallback(() => {
    setSelectedNodeId('center')
    setExpandedTopicIds([])
    onResetView()
    window.setTimeout(() => {
      void setCenter(140, 62, {
        zoom: MIND_MAP_DEFAULT_ZOOM,
        duration: 240,
      })
    }, 40)
  }, [onResetView, setCenter])
  const graph = useMemo(
    () =>
      selectedRole
        ? buildLearningGraph({
            selectedRole,
            branches: mindMapBranches,
            collapsedBranchIds,
            selectedNodeId,
            expandedTopicIds,
            roleProfileResult,
          })
        : { nodes: [], edges: [] },
    [
      collapsedBranchIds,
      expandedTopicIds,
      mindMapBranches,
      roleProfileResult,
      selectedNodeId,
      selectedRole,
    ],
  )

  useEffect(() => {
    const currentViewport = getViewport()
    void setViewport(
      { ...currentViewport, zoom: mindMapZoom },
      { duration: 180 },
    )
  }, [getViewport, mindMapZoom, setViewport])

  useEffect(() => {
    setSelectedNodeId('center')
    setExpandedTopicIds([])
  }, [selectedRole?.name])

  useEffect(() => {
    setExpandedTopicIds((currentIds) =>
      currentIds.filter((topicId) => allTopicNodeIds.includes(topicId)),
    )
  }, [allTopicNodeIds])

  useEffect(() => () => clearNodeClickTimer(), [clearNodeClickTimer])

  const handleNodeClick = useCallback(
    (node: Node<LearningNodeData>) => {
      clearNodeClickTimer()
      clickTimerRef.current = window.setTimeout(() => {
        clickTimerRef.current = null
        const nodeData = node.data
        setSelectedNodeId(node.id)
        if (
          nodeData.kind === 'branch' &&
          nodeData.branchId &&
          nodeData.isCollapsed
        ) {
          handleToggleBranch(nodeData.branchId)
        }
        if (nodeData.kind === 'topic') {
          expandTopic(node.id)
        }
        window.setTimeout(() => focusNode(node.id, nodeData), 40)
      }, 180)
    },
    [clearNodeClickTimer, expandTopic, focusNode, handleToggleBranch],
  )

  const handleNodeDoubleClick = useCallback(
    (node: Node<LearningNodeData>) => {
      clearNodeClickTimer()
      const nodeData = node.data
      setSelectedNodeId(node.id)
      if (
        nodeData.kind === 'branch' &&
        nodeData.branchId &&
        !nodeData.isCollapsed
      ) {
        handleToggleBranch(nodeData.branchId)
      }
      if (nodeData.kind === 'topic' && nodeData.isExpanded) {
        collapseTopic(node.id)
      }
      window.setTimeout(() => focusNode(node.id, nodeData), 40)
    },
    [clearNodeClickTimer, collapseTopic, focusNode, handleToggleBranch],
  )

  return (
    <section className="records-section learning-section" id="learning">
      <div className="section-heading learning-heading">
        <div>
          <p className="eyebrow">Learning Map</p>
          <h3>{selectedRole ? `${selectedRole.name}学习地图` : '学习地图'}</h3>
          {roleProfileResult ? (
            <p className="learning-source-note">
              LLM地图：{roleProfileResult.provider} · {roleProfileResult.mode}
            </p>
          ) : null}
        </div>
        <div className="mindmap-toolbar" aria-label="学习地图工具">
          {selectedRole ? (
            <button
              type="button"
              onClick={() => onGenerateRoleProfile(selectedRole.name)}
              disabled={generatingRoleProfileName === selectedRole.name}
            >
              {generatingRoleProfileName === selectedRole.name
                ? '生成中'
                : roleProfileResult
                  ? '重新生成'
                  : 'LLM生成'}
            </button>
          ) : null}
          <button type="button" onClick={() => onZoom(-0.08)}>
            缩小
          </button>
          <span>{Math.round(mindMapZoom * 100)}%</span>
          <button type="button" onClick={() => onZoom(0.08)}>
            放大
          </button>
          <button type="button" onClick={resetWholeMap}>
            复位
          </button>
          <button type="button" onClick={expandWholeMap}>
            全部展开
          </button>
        </div>
      </div>

      {roleSummaries.length > 0 ? (
        <div className="learning-role-selector" aria-label="学习地图岗位大类选择">
          <div>
            <strong>岗位大类</strong>
            <span>
              当前地图只聚合所选大类的岗位样本，不同大类会生成不同学习路径。
            </span>
          </div>
          <div className="learning-role-tabs">
            {roleSummaries.map((role) => (
              <button
                key={role.name}
                className={selectedRole?.name === role.name ? 'selected' : ''}
                type="button"
                onClick={() => {
                  setSelectedNodeId('center')
                  onSelectedRoleChange(role.name)
                }}
              >
                <span>{role.name}</span>
                <small>{role.jobCount} 个岗位样本</small>
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {!selectedRole ? (
        <div className="empty-state">
          <p>还没有可生成学习地图的岗位大类。</p>
        </div>
      ) : (
        <div className="learning-map-workspace">
          <div className="mindmap-stage xmind-stage" role="region" aria-label="学习地图画布">
            <ReactFlow
              nodes={graph.nodes}
              edges={graph.edges}
              nodeTypes={nodeTypes}
              nodesDraggable
              nodesConnectable={false}
              elementsSelectable
              fitView
              fitViewOptions={{ padding: 0.24 }}
              minZoom={0.28}
              maxZoom={1.5}
              defaultViewport={{ x: 0, y: 0, zoom: mindMapZoom }}
              onNodeClick={(_, node) => handleNodeClick(node)}
              onNodeDoubleClick={(_, node) => handleNodeDoubleClick(node)}
            >
              <Background color="var(--mindmap-grid-line)" gap={30} size={1} />
              <Controls showInteractive={false} />
              <MiniMap
                nodeColor={(node) =>
                  typeof node.data?.color === 'string' ? node.data.color : '#0f8f88'
                }
                pannable
                zoomable
              />
              <Panel className="mindmap-flow-panel" position="top-left">
                <strong>{selectedRole.name}</strong>
                <span>{graph.nodes.length} 个节点</span>
              </Panel>
            </ReactFlow>
          </div>
        </div>
      )}
    </section>
  )
}

function LearningNode({ data }: NodeProps<Node<LearningNodeData>>) {
  const isTopic = data.kind === 'topic'
  const targetPosition = data.side === 'left' ? Position.Right : Position.Left
  const sourcePosition = data.side === 'left' ? Position.Left : Position.Right
  return (
    <div
      className={`learning-flow-node xmind-node ${data.kind} ${
        data.isSelected ? 'selected' : ''
      } ${data.isExpanded ? 'expanded' : ''} ${data.isCollapsed ? 'collapsed' : ''}`}
      style={{ '--node-color': data.color } as CSSProperties}
    >
      {data.kind !== 'center' ? (
        <Handle className="learning-node-handle" type="target" position={targetPosition} />
      ) : null}
      {data.kind !== 'topic' ? (
        <Handle className="learning-node-handle" type="source" position={sourcePosition} />
      ) : null}
      <div className="xmind-node-main">
        <span>{kindLabels[data.kind]}</span>
        <strong>{data.title}</strong>
        {data.subtitle ? <small>{data.subtitle}</small> : null}
      </div>
      {isTopic && data.isExpanded ? (
        <div className="xmind-node-detail">
          <ul>
            {data.evidence.slice(0, 3).map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  )
}

function buildLearningGraph({
  selectedRole,
  branches,
  collapsedBranchIds,
  selectedNodeId,
  expandedTopicIds,
  roleProfileResult,
}: {
  selectedRole: RoleSummary
  branches: MindMapBranch[]
  collapsedBranchIds: string[]
  selectedNodeId: string
  expandedTopicIds: string[]
  roleProfileResult: LLMRoleProfileResult | null
}): LearningGraph {
  const nodes: Node<LearningNodeData>[] = []
  const edges: Edge[] = []
  const sourceLabel = roleProfileResult ? 'LLM生成，基于岗位大类聚合' : '本地岗位卡聚合'
  const centerData: LearningNodeData = {
    nodeId: 'center',
    title: selectedRole.name,
    subtitle: `${selectedRole.jobCount} 个岗位样本`,
    kind: 'center',
    color: '#263a37',
    sourceLabel,
    evidence: [
      ...selectedRole.titles.slice(0, 4),
      ...selectedRole.companies.slice(0, 3),
    ],
    isSelected: selectedNodeId === 'center',
    childCount: branches.length,
  }

  nodes.push({
    id: 'center',
    type: 'learningNode',
    position: { x: 0, y: 0 },
    data: centerData,
  })

  const leftBranches = branches.filter((branch) => branch.side === 'left')
  const rightBranches = branches.filter((branch) => branch.side === 'right')
  const branchCenterYById = {
    ...computeBranchCenterYById(
      leftBranches,
      collapsedBranchIds,
      expandedTopicIds,
      selectedRole,
    ),
    ...computeBranchCenterYById(
      rightBranches,
      collapsedBranchIds,
      expandedTopicIds,
      selectedRole,
    ),
  }

  branches.forEach((branch) => {
    const branchCenterY = branchCenterYById[branch.id] ?? 0
    const branchY = branchCenterY - BRANCH_NODE_HEIGHT / 2
    const branchX = branch.side === 'left' ? -BRANCH_X : BRANCH_X
    const isCollapsed = collapsedBranchIds.includes(branch.id)
    const branchNodeId = `branch-${branch.id}`
    const branchData: LearningNodeData = {
      nodeId: branchNodeId,
      title: branch.title,
      subtitle: isCollapsed ? `${branch.items.length} 个学习点待展开` : `${branch.items.length} 个学习点`,
      kind: 'branch',
      color: branch.color,
      side: branch.side,
      branchId: branch.id,
      sourceLabel,
      evidence: branch.items.slice(0, 5),
      isCollapsed,
      isSelected: selectedNodeId === branchNodeId,
      childCount: branch.items.length,
    }

    nodes.push({
      id: branchNodeId,
      type: 'learningNode',
      position: { x: branchX, y: branchY },
      data: branchData,
    })
    edges.push({
      id: `edge-center-${branch.id}`,
      source: 'center',
      target: branchNodeId,
      type: 'smoothstep',
      animated: Boolean(roleProfileResult),
      style: { stroke: branch.color, strokeWidth: 3 },
    })

    if (isCollapsed) return

    const visibleItems = branch.items.slice(0, 10)
    const expandedTopicIndexes = expandedTopicIndexesForBranch(
      branch,
      expandedTopicIds,
    )
    const topicCenterOffsets = computeTopicCenterOffsets(
      visibleItems,
      expandedTopicIndexes,
      selectedRole,
    )

    visibleItems.forEach((item, itemIndex) => {
      const topicNodeId = `topic-${branch.id}-${itemIndex}`
      const isSelected = selectedNodeId === topicNodeId
      const isExpanded = expandedTopicIds.includes(topicNodeId)
      const evidence = buildTopicEvidence(item, selectedRole)
      const topicData: LearningNodeData = {
        nodeId: topicNodeId,
        title: item,
        kind: 'topic',
        color: branch.color,
        side: branch.side,
        branchId: branch.id,
        branchTitle: branch.title,
        sourceLabel,
        evidence,
        isSelected,
        isExpanded,
      }
      const topicHeight = estimateTopicNodeHeight(item, evidence, isExpanded)
      const topicX =
        branch.side === 'left'
          ? -TOPIC_X - (isExpanded ? LEFT_TOPIC_SELECTED_EXTRA_WIDTH : 0)
          : TOPIC_X
      const topicY = branchCenterY + topicCenterOffsets[itemIndex] - topicHeight / 2

      nodes.push({
        id: topicNodeId,
        type: 'learningNode',
        position: { x: topicX, y: topicY },
        data: topicData,
      })
      edges.push({
        id: `edge-${branch.id}-${itemIndex}`,
        source: branchNodeId,
        target: topicNodeId,
        type: 'smoothstep',
        style: { stroke: branch.color, strokeWidth: 2, opacity: 0.75 },
      })
    })
  })

  return { nodes, edges }
}

function computeBranchCenterYById(
  branches: MindMapBranch[],
  collapsedBranchIds: string[],
  expandedTopicIds: string[],
  role: RoleSummary,
): Record<string, number> {
  const laneHeights = branches.map((branch) =>
    measureBranchLaneHeight(branch, collapsedBranchIds, expandedTopicIds, role),
  )
  const totalHeight =
    laneHeights.reduce<number>((sum, height) => sum + height, 0) +
    Math.max(0, branches.length - 1) * BRANCH_LANE_GAP
  let cursor = -totalHeight / 2
  return branches.reduce<Record<string, number>>((centerYById, branch, index) => {
    const laneHeight = laneHeights[index] ?? COLLAPSED_BRANCH_LANE_HEIGHT
    centerYById[branch.id] = cursor + laneHeight / 2
    cursor += laneHeight + BRANCH_LANE_GAP
    return centerYById
  }, {})
}

function measureBranchLaneHeight(
  branch: MindMapBranch,
  collapsedBranchIds: string[],
  expandedTopicIds: string[],
  role: RoleSummary,
): number {
  if (collapsedBranchIds.includes(branch.id)) {
    return COLLAPSED_BRANCH_LANE_HEIGHT
  }

  const expandedIndexes = expandedTopicIndexesForBranch(branch, expandedTopicIds)
  const topicStackHeight = measureTopicStackHeight(
    branch.items.slice(0, 10),
    expandedIndexes,
    role,
  )
  return Math.max(MIN_EXPANDED_BRANCH_LANE_HEIGHT, topicStackHeight + 96)
}

function expandedTopicIndexesForBranch(
  branch: MindMapBranch,
  expandedTopicIds: string[],
): Set<number> {
  const prefix = `topic-${branch.id}-`
  const indexes = expandedTopicIds
    .filter((topicId) => topicId.startsWith(prefix))
    .map((topicId) => Number(topicId.replace(prefix, '')))
    .filter(Number.isFinite)
  return new Set(indexes)
}

function measureTopicStackHeight(
  items: string[],
  expandedIndexes: Set<number>,
  role: RoleSummary,
): number {
  if (items.length <= 0) return 0
  return items.reduce<number>((height, item, index) => {
    const nodeHeight = estimateTopicNodeHeight(
      item,
      buildTopicEvidence(item, role),
      expandedIndexes.has(index),
    )
    return height + nodeHeight + (index === items.length - 1 ? 0 : TOPIC_ROW_GAP)
  }, 0)
}

function computeTopicCenterOffsets(
  items: string[],
  expandedIndexes: Set<number>,
  role: RoleSummary,
): number[] {
  const totalHeight = measureTopicStackHeight(items, expandedIndexes, role)
  let cursor = -totalHeight / 2
  return items.map((item, index) => {
    const nodeHeight = estimateTopicNodeHeight(
      item,
      buildTopicEvidence(item, role),
      expandedIndexes.has(index),
    )
    const centerOffset = cursor + nodeHeight / 2
    cursor += nodeHeight + TOPIC_ROW_GAP
    return centerOffset
  })
}

function buildAllTopicNodeIds(branches: MindMapBranch[]): string[] {
  return branches.flatMap((branch) =>
    branch.items.slice(0, 10).map((_, index) => `topic-${branch.id}-${index}`),
  )
}

function estimateTopicNodeHeight(
  title: string,
  evidence: string[],
  isExpanded: boolean,
): number {
  const titleLines = estimateTextLines(title, isExpanded ? 28 : 20)
  const titleBlockHeight = 38 + titleLines * 26

  if (!isExpanded) {
    return Math.max(MIN_TOPIC_NODE_HEIGHT, titleBlockHeight)
  }

  const evidenceItems = evidence.slice(0, 3)
  const evidenceLineCount = evidenceItems.reduce(
    (lineCount, item) => lineCount + estimateTextLines(item, 34),
    0,
  )
  const evidenceHeight =
    evidenceItems.length > 0
      ? 20 + evidenceLineCount * 22 + Math.max(0, evidenceItems.length - 1) * 6
      : 0

  return Math.max(
    MIN_EXPANDED_TOPIC_NODE_HEIGHT,
    titleBlockHeight + evidenceHeight + 18,
  )
}

function estimateTextLines(text: string, charsPerLine: number): number {
  const weightedLength = Array.from(text).reduce((length, char) => {
    return length + (char.charCodeAt(0) <= 127 ? 0.55 : 1)
  }, 0)
  return Math.max(1, Math.ceil(weightedLength / charsPerLine))
}

function buildTopicEvidence(item: string, role: RoleSummary) {
  const evidencePool = [
    ...role.topSkills,
    ...role.commonRequirements,
    ...role.commonResponsibilities,
    ...role.commonBonusPoints,
  ]
  const matched = evidencePool.filter((candidate) =>
    candidate.toLowerCase().includes(item.toLowerCase()),
  )
  return matched.length ? matched.slice(0, 3) : [item]
}

const kindLabels: Record<LearningNodeKind, string> = {
  center: '岗位大类',
  branch: '能力域',
  topic: '学习点',
}

export default LearningMindMap
