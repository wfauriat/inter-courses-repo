import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ChangeEvent,
} from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  BaseEdge,
  EdgeLabelRenderer,
  MarkerType,
  getSmoothStepPath,
  useNodesState,
  useEdgesState,
  useReactFlow,
  addEdge,
  type Connection,
  type Node,
  type Edge,
  type EdgeProps,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import * as dagre from '@dagrejs/dagre'

const EDGE_TYPES = [
  'supports',
  'opposes',
  'qualifies',
  'instantiates',
  'responds-to',
  'synthesizes',
  'depends-on',
  'defers-to',
] as const
type EdgeType = (typeof EDGE_TYPES)[number]

/* === authoring features (provisional) === */
const AUTHORING_FEATURES = true
const CLUSTER_IDS = [
  'disposition',
  'inference',
  'frame_problem',
  'decision_making',
  'modern_context',
] as const
type ClusterId = (typeof CLUSTER_IDS)[number]
/* === end authoring features === */

type CardNodeData = {
  label: string
  body: string
  /* === authoring features (provisional) === */
  core_claim?: boolean
  core_theory?: boolean
  illustration?: boolean
  isStructural?: boolean
  main_cluster?: ClusterId
  /* === end authoring features === */
}
type CardEdgeData = {
  edgeType: EdgeType
  labelOffsetX?: number
  labelOffsetY?: number
}
type CardNode = Node<CardNodeData>
type CardEdge = Edge<CardEdgeData>

const FILE_VERSION = '0.1'
const ARROW_COLOR = '#9ca3af'
const LAYOUT_NODE_W = 210
const LAYOUT_NODE_H = 56

function CardEdgeComponent(props: EdgeProps) {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    label,
    data,
    style,
    markerEnd,
    selected,
  } = props
  const { setEdges, getViewport } = useReactFlow()

  const [path, defaultLabelX, defaultLabelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 0,
  })

  const d = data as
    | { labelOffsetX?: number; labelOffsetY?: number }
    | undefined
  const offsetX = d?.labelOffsetX ?? 0
  const offsetY = d?.labelOffsetY ?? 0
  const labelX = defaultLabelX + offsetX
  const labelY = defaultLabelY + offsetY

  const dragRef = useRef<{
    startClientX: number
    startClientY: number
    startOffsetX: number
    startOffsetY: number
  } | null>(null)

  const onLabelMouseDown = (e: React.MouseEvent) => {
    e.stopPropagation()
    e.preventDefault()
    dragRef.current = {
      startClientX: e.clientX,
      startClientY: e.clientY,
      startOffsetX: offsetX,
      startOffsetY: offsetY,
    }
    const onMove = (ev: MouseEvent) => {
      if (!dragRef.current) return
      const { zoom } = getViewport()
      const dx = (ev.clientX - dragRef.current.startClientX) / zoom
      const dy = (ev.clientY - dragRef.current.startClientY) / zoom
      setEdges((eds) =>
        eds.map((edge) =>
          edge.id === id
            ? {
                ...edge,
                data: {
                  ...edge.data,
                  labelOffsetX: dragRef.current!.startOffsetX + dx,
                  labelOffsetY: dragRef.current!.startOffsetY + dy,
                },
              }
            : edge,
        ),
      )
    }
    const onUp = () => {
      dragRef.current = null
      document.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseup', onUp)
    }
    document.addEventListener('mousemove', onMove)
    document.addEventListener('mouseup', onUp)
  }

  const hasLabel =
    typeof label === 'string' ? label.length > 0 : label != null

  return (
    <>
      <BaseEdge path={path} style={style} markerEnd={markerEnd} />
      {hasLabel && (
        <EdgeLabelRenderer>
          <div
            className={`edge-label-floating${selected ? ' selected' : ''}`}
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: 'all',
              cursor: 'move',
            }}
            onMouseDown={onLabelMouseDown}
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  )
}

const customEdgeTypes = { 'card-edge': CardEdgeComponent }

function autoLayout(
  nodes: CardNode[],
  edges: CardEdge[],
  direction: 'LR' | 'TB' = 'LR',
): CardNode[] {
  if (nodes.length === 0) return nodes
  const g = new dagre.graphlib.Graph()
  g.setGraph({ rankdir: direction, nodesep: 60, ranksep: 140 })
  g.setDefaultEdgeLabel(() => ({}))
  nodes.forEach((n) =>
    g.setNode(n.id, { width: LAYOUT_NODE_W, height: LAYOUT_NODE_H }),
  )
  edges.forEach((e) => g.setEdge(e.source, e.target))
  dagre.layout(g)
  return nodes.map((n) => {
    const pos = g.node(n.id)
    return {
      ...n,
      position: {
        x: pos.x - LAYOUT_NODE_W / 2,
        y: pos.y - LAYOUT_NODE_H / 2,
      },
    }
  })
}

const initialNodes: CardNode[] = [
  {
    id: 'central_claim',
    position: { x: 0, y: 0 },
    data: { label: 'central_claim', body: '' },
  },
]
const initialEdges: CardEdge[] = []

type Theme = 'light' | 'dark'

function App() {
  const idRef = useRef(2)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const fitViewRef = useRef<((opts?: { duration?: number }) => void) | null>(
    null,
  )

  const [nodes, setNodes, onNodesChange] = useNodesState<CardNode>(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState<CardEdge>(initialEdges)
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(
    'central_claim',
  )
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null)
  const [editingEdgeId, setEditingEdgeId] = useState<string | null>(null)
  const [editingField, setEditingField] = useState<'label' | 'body' | null>(
    null,
  )
  const [revealMode, setRevealMode] = useState(true)
  const [walkedEdgeIds, setWalkedEdgeIds] = useState<Set<string>>(
    () => new Set(),
  )
  const [theme, setTheme] = useState<Theme>(() =>
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light',
  )
  const [rightPaneWidth, setRightPaneWidth] = useState<number>(() =>
    typeof window !== 'undefined'
      ? Math.max(380, Math.round(window.innerWidth * 0.38))
      : 460,
  )
  const [isResizing, setIsResizing] = useState(false)
  /* === authoring features (provisional) === */
  const [showCoreClaim, setShowCoreClaim] = useState(false)
  const [showCoreTheory, setShowCoreTheory] = useState(false)
  const [showIllustration, setShowIllustration] = useState(false)
  const [showStructural, setShowStructural] = useState(false)
  const [showClusters, setShowClusters] = useState(false)
  /* === end authoring features === */

  const onSplitterMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault()
      const startX = e.clientX
      const startWidth = rightPaneWidth
      setIsResizing(true)
      document.body.style.userSelect = 'none'
      document.body.style.cursor = 'col-resize'
      const onMove = (ev: MouseEvent) => {
        const dx = startX - ev.clientX
        const next = Math.min(
          Math.max(startWidth + dx, 320),
          window.innerWidth - 320,
        )
        setRightPaneWidth(next)
      }
      const onUp = () => {
        document.removeEventListener('mousemove', onMove)
        document.removeEventListener('mouseup', onUp)
        document.body.style.userSelect = ''
        document.body.style.cursor = ''
        setIsResizing(false)
      }
      document.addEventListener('mousemove', onMove)
      document.addEventListener('mouseup', onUp)
    },
    [rightPaneWidth],
  )

  useEffect(() => {
    document.documentElement.dataset.theme = theme
  }, [theme])

  useEffect(() => {
    setEditingField(null)
  }, [selectedNodeId])

  const onConnect = useCallback(
    (params: Connection) => {
      const id = `e_${params.source}_${params.target}_${Date.now()}`
      const newEdge: CardEdge = {
        ...params,
        id,
        label: '',
        data: { edgeType: 'supports' },
      }
      setEdges((eds) => addEdge(newEdge, eds))
      setWalkedEdgeIds((prev) => {
        const next = new Set(prev)
        next.add(id)
        return next
      })
    },
    [setEdges],
  )

  const walkEdge = useCallback(
    (edgeId: string, targetId: string) => {
      setWalkedEdgeIds((prev) => {
        const next = new Set(prev)
        next.add(edgeId)
        return next
      })
      setSelectedNodeId(targetId)
      setSelectedEdgeId(null)
      setEditingEdgeId(null)
      setNodes((nds) =>
        nds.map((n) => ({ ...n, selected: n.id === targetId })),
      )
    },
    [setNodes],
  )

  const showAllLinks = useCallback(() => {
    setRevealMode(false)
  }, [])

  const resetWalk = useCallback(() => {
    setWalkedEdgeIds(new Set())
    setRevealMode(true)
  }, [])

  const addNode = useCallback(() => {
    const id = `node_${idRef.current++}`
    setNodes((nds) => [
      ...nds,
      {
        id,
        position: {
          x: Math.random() * 400 - 200,
          y: Math.random() * 300 - 150,
        },
        data: { label: id, body: '' },
      },
    ])
    setSelectedNodeId(id)
    setSelectedEdgeId(null)
    setEditingEdgeId(null)
  }, [setNodes])

  const onNodesDelete = useCallback(
    (deleted: Node[]) => {
      if (deleted.some((n) => n.id === selectedNodeId)) {
        setSelectedNodeId(null)
      }
    },
    [selectedNodeId],
  )

  const updateNodeData = useCallback(
    (id: string, partial: Partial<CardNodeData>) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id ? { ...n, data: { ...n.data, ...partial } } : n,
        ),
      )
    },
    [setNodes],
  )

  const deleteNode = useCallback(
    (id: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== id))
      setEdges((eds) =>
        eds.filter((e) => e.source !== id && e.target !== id),
      )
      if (selectedNodeId === id) setSelectedNodeId(null)
    },
    [setNodes, setEdges, selectedNodeId],
  )

  const updateEdge = useCallback(
    (id: string, partial: { label?: string; edgeType?: EdgeType }) => {
      setEdges((eds) =>
        eds.map((e) => {
          if (e.id !== id) return e
          return {
            ...e,
            label: partial.label !== undefined ? partial.label : e.label,
            data: {
              edgeType: partial.edgeType ?? e.data?.edgeType ?? 'supports',
            },
          }
        }),
      )
    },
    [setEdges],
  )

  const deleteEdge = useCallback(
    (id: string) => {
      const edge = edges.find((e) => e.id === id)
      if (!edge) return
      const labelPart =
        typeof edge.label === 'string' && edge.label
          ? `\n\n"${edge.label}"`
          : ''
      const ok = window.confirm(`Delete this edge?${labelPart}`)
      if (!ok) return
      setEdges((eds) => eds.filter((e) => e.id !== id))
      if (selectedEdgeId === id) setSelectedEdgeId(null)
      if (editingEdgeId === id) setEditingEdgeId(null)
    },
    [edges, setEdges, selectedEdgeId, editingEdgeId],
  )

  const applyAutoLayout = useCallback(() => {
    const newNodes = autoLayout(nodes, edges, 'TB')
    setNodes(newNodes)
    window.requestAnimationFrame(() => {
      fitViewRef.current?.({ duration: 400 })
    })
  }, [nodes, edges, setNodes])

  const clearAll = useCallback(() => {
    const ok = window.confirm(
      'Clear all nodes and edges? This cannot be undone.',
    )
    if (!ok) return
    setNodes([])
    setEdges([])
    setSelectedNodeId(null)
    setSelectedEdgeId(null)
    setEditingEdgeId(null)
    setWalkedEdgeIds(new Set())
    setRevealMode(true)
    idRef.current = 2
  }, [setNodes, setEdges])

  const saveToFile = useCallback(() => {
    const data = {
      version: FILE_VERSION,
      nodes: nodes.map((n) => ({
        id: n.id,
        position: n.position,
        data: n.data,
      })),
      edges: edges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle ?? null,
        targetHandle: e.targetHandle ?? null,
        label: typeof e.label === 'string' ? e.label : '',
        data: e.data,
      })),
    }
    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: 'application/json',
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `argument-canvas-${new Date()
      .toISOString()
      .slice(0, 10)}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [nodes, edges])

  const onFileSelected = useCallback(
    async (e: ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0]
      if (!file) return
      try {
        const text = await file.text()
        const parsed = JSON.parse(text) as unknown
        if (typeof parsed !== 'object' || parsed === null) {
          throw new Error('file is not a valid object')
        }
        const rec = parsed as Record<string, unknown>
        const rawNodes: unknown[] = Array.isArray(rec.nodes) ? rec.nodes : []
        const rawEdges: unknown[] = Array.isArray(rec.edges) ? rec.edges : []

        const loadedNodes: CardNode[] = rawNodes.flatMap((raw): CardNode[] => {
          if (typeof raw !== 'object' || raw === null) return []
          const r = raw as Record<string, unknown>
          if (typeof r.id !== 'string') return []
          const pos = r.position as Record<string, unknown> | undefined
          const data = r.data as Record<string, unknown> | undefined
          /* === authoring features (provisional) === */
          const cluster =
            typeof data?.main_cluster === 'string' &&
            (CLUSTER_IDS as readonly string[]).includes(data.main_cluster)
              ? (data.main_cluster as ClusterId)
              : undefined
          const authoring: Partial<CardNodeData> = {
            ...(data?.core_claim === true && { core_claim: true }),
            ...(data?.core_theory === true && { core_theory: true }),
            ...(data?.illustration === true && { illustration: true }),
            ...(data?.isStructural === true && { isStructural: true }),
            ...(cluster && { main_cluster: cluster }),
          }
          /* === end authoring features === */
          return [
            {
              id: r.id,
              position: {
                x: typeof pos?.x === 'number' ? pos.x : 0,
                y: typeof pos?.y === 'number' ? pos.y : 0,
              },
              data: {
                label: typeof data?.label === 'string' ? data.label : '',
                body: typeof data?.body === 'string' ? data.body : '',
                ...authoring,
              },
            },
          ]
        })

        const loadedEdges: CardEdge[] = rawEdges.flatMap((raw): CardEdge[] => {
          if (typeof raw !== 'object' || raw === null) return []
          const r = raw as Record<string, unknown>
          if (
            typeof r.id !== 'string' ||
            typeof r.source !== 'string' ||
            typeof r.target !== 'string'
          )
            return []
          const data = r.data as Record<string, unknown> | undefined
          const candidate = data?.edgeType
          const edgeType: EdgeType =
            typeof candidate === 'string' &&
            (EDGE_TYPES as readonly string[]).includes(candidate)
              ? (candidate as EdgeType)
              : 'supports'
          const labelOffsetX =
            typeof data?.labelOffsetX === 'number' ? data.labelOffsetX : 0
          const labelOffsetY =
            typeof data?.labelOffsetY === 'number' ? data.labelOffsetY : 0
          return [
            {
              id: r.id,
              source: r.source,
              target: r.target,
              sourceHandle:
                typeof r.sourceHandle === 'string' ? r.sourceHandle : null,
              targetHandle:
                typeof r.targetHandle === 'string' ? r.targetHandle : null,
              label: typeof r.label === 'string' ? r.label : '',
              data: { edgeType, labelOffsetX, labelOffsetY },
            },
          ]
        })

        setNodes(loadedNodes)
        setEdges(loadedEdges)
        setSelectedNodeId(null)
        setSelectedEdgeId(null)
        setEditingEdgeId(null)
        setWalkedEdgeIds(new Set())
        setRevealMode(true)
        idRef.current = loadedNodes.reduce((acc, n) => {
          const m = /^node_(\d+)$/.exec(n.id)
          return m ? Math.max(acc, parseInt(m[1], 10) + 1) : acc
        }, 2)
        window.requestAnimationFrame(() => {
          fitViewRef.current?.({ duration: 300 })
        })
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'unknown error'
        window.alert(`Failed to load: ${msg}`)
      }
      e.target.value = ''
    },
    [setNodes, setEdges],
  )

  const selectedNode = useMemo(
    () => nodes.find((n) => n.id === selectedNodeId) ?? null,
    [nodes, selectedNodeId],
  )

  const outgoingEdges = useMemo(
    () => edges.filter((e) => e.source === selectedNodeId),
    [edges, selectedNodeId],
  )

  /* === authoring features (provisional) === */
  const incomingCount = useMemo(
    () =>
      selectedNodeId
        ? edges.filter((e) => e.target === selectedNodeId).length
        : 0,
    [edges, selectedNodeId],
  )
  /* === end authoring features === */

  const styledNodes = useMemo(
    () =>
      nodes.map((n) => {
        const classes: string[] = []
        if (n.id === selectedNodeId) classes.push('node-focused')
        /* === authoring features (provisional) === */
        if (AUTHORING_FEATURES) {
          if (showCoreClaim && n.data.core_claim) classes.push('flag-core-claim')
          if (showCoreTheory && n.data.core_theory)
            classes.push('flag-core-theory')
          if (showIllustration && n.data.illustration)
            classes.push('flag-illustration')
          if (showStructural && n.data.isStructural)
            classes.push('flag-structural')
          if (showClusters && n.data.main_cluster)
            classes.push(`cluster-${n.data.main_cluster}`)
        }
        /* === end authoring features === */
        return {
          ...n,
          className: classes.join(' '),
          data: { ...n.data, label: n.data.label || n.id },
        }
      }),
    [
      nodes,
      selectedNodeId,
      showCoreClaim,
      showCoreTheory,
      showIllustration,
      showStructural,
      showClusters,
    ],
  )

  const visibleEdges = useMemo(() => {
    if (!revealMode) return edges
    return edges.filter(
      (e) => walkedEdgeIds.has(e.id) || e.source === selectedNodeId,
    )
  }, [edges, revealMode, walkedEdgeIds, selectedNodeId])

  const styledEdges = useMemo(
    () =>
      visibleEdges.map((e) => {
        const isSuggested = e.source === selectedNodeId
        const isSelected = e.id === selectedEdgeId
        const isWalked = walkedEdgeIds.has(e.id)
        const cls = [
          isWalked ? 'edge-walked' : '',
          isSuggested ? 'edge-suggested' : '',
          isSelected ? 'edge-selected' : '',
        ]
          .filter(Boolean)
          .join(' ')
        return {
          ...e,
          className: cls,
          animated: isSuggested,
        }
      }),
    [visibleEdges, selectedNodeId, selectedEdgeId, walkedEdgeIds],
  )

  return (
    <div
      className="app"
      style={{
        gridTemplateColumns: `minmax(0, 1fr) 6px ${rightPaneWidth}px`,
      }}
    >
      <div className="canvas-pane">
        <div className="toolbar">
          <button onClick={addNode}>Add node</button>
          <button onClick={saveToFile}>Save</button>
          <button onClick={() => fileInputRef.current?.click()}>Load</button>
          <button onClick={clearAll}>Clear</button>
          <button onClick={applyAutoLayout}>Auto-layout</button>
          <button onClick={showAllLinks}>Show all</button>
          <button onClick={resetWalk}>Reset walk</button>
          <button
            onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}
          >
            {theme === 'light' ? 'Dark' : 'Light'} mode
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="application/json,.json"
            onChange={onFileSelected}
            style={{ display: 'none' }}
          />
          <span className="hint">
            click node to focus · click edge to select · double-click edge
            label to edit · drag handle to connect
          </span>
        </div>
        <ReactFlow
          nodes={styledNodes}
          edges={styledEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodesDelete={onNodesDelete}
          onConnect={onConnect}
          onNodeClick={(_, node) => {
            setSelectedNodeId(node.id)
            setSelectedEdgeId(null)
            setEditingEdgeId(null)
          }}
          onEdgeClick={(_, edge) => {
            setSelectedEdgeId(edge.id)
          }}
          onPaneClick={() => {
            setSelectedNodeId(null)
            setSelectedEdgeId(null)
            setEditingEdgeId(null)
          }}
          onInit={(instance) => {
            fitViewRef.current = (opts) => instance.fitView(opts)
          }}
          edgeTypes={customEdgeTypes}
          defaultEdgeOptions={{
            type: 'card-edge',
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: 18,
              height: 18,
              color: ARROW_COLOR,
            },
          }}
          deleteKeyCode={['Backspace', 'Delete']}
          colorMode={theme}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap pannable zoomable />
        </ReactFlow>
        {/* === authoring toolbar (provisional) === */}
        {AUTHORING_FEATURES && (
          <div className="authoring-toolbar">
            <button
              className={showCoreClaim ? 'active' : ''}
              onClick={() => setShowCoreClaim((v) => !v)}
              title="Highlight core_claim nodes (thick border)"
            >
              core claim
            </button>
            <button
              className={showCoreTheory ? 'active' : ''}
              onClick={() => setShowCoreTheory((v) => !v)}
              title="Highlight core_theory nodes (dashed border)"
            >
              core theory
            </button>
            <button
              className={showIllustration ? 'active' : ''}
              onClick={() => setShowIllustration((v) => !v)}
              title="Highlight illustration nodes (dotted border)"
            >
              illustration
            </button>
            <button
              className={showStructural ? 'active' : ''}
              onClick={() => setShowStructural((v) => !v)}
              title="Highlight structural spine nodes (outline ring)"
            >
              structural
            </button>
            <button
              className={showClusters ? 'active' : ''}
              onClick={() => setShowClusters((v) => !v)}
              title="Color nodes by main_cluster"
            >
              cluster
            </button>
          </div>
        )}
        {/* === end authoring toolbar === */}
      </div>
      <div
        className={`splitter${isResizing ? ' dragging' : ''}`}
        onMouseDown={onSplitterMouseDown}
        role="separator"
        aria-orientation="vertical"
      />
      <aside className="right-pane">
        <section className="content-pane">
          {selectedNode ? (
            <>
              <div className="content-header">
                {editingField === 'label' ? (
                  <input
                    autoFocus
                    className="node-label-input"
                    type="text"
                    value={selectedNode.data.label}
                    onChange={(e) =>
                      updateNodeData(selectedNode.id, {
                        label: e.target.value,
                      })
                    }
                    onBlur={() => setEditingField(null)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') {
                        ;(e.target as HTMLInputElement).blur()
                      } else if (e.key === 'Escape') {
                        setEditingField(null)
                      }
                    }}
                    placeholder={selectedNode.id}
                  />
                ) : (
                  <h2
                    className="node-label-display"
                    title="Double-click to edit"
                    onDoubleClick={() => setEditingField('label')}
                  >
                    {selectedNode.data.label || (
                      <span className="placeholder-inline">
                        {selectedNode.id}
                      </span>
                    )}
                  </h2>
                )}
                <button
                  className="icon-button danger"
                  title="Delete node"
                  onClick={() => deleteNode(selectedNode.id)}
                >
                  Delete
                </button>
              </div>
              {/* === authoring features (provisional) === */}
              {AUTHORING_FEATURES && (
                <div className="node-meta">
                  <span title="incoming edges">← {incomingCount} in</span>
                  <span className="node-meta-sep">·</span>
                  <span title="outgoing edges">
                    → {outgoingEdges.length} out
                  </span>
                </div>
              )}
              {/* === end authoring features === */}
              {editingField === 'body' ? (
                <textarea
                  autoFocus
                  className="node-body-input"
                  value={selectedNode.data.body}
                  onChange={(e) =>
                    updateNodeData(selectedNode.id, { body: e.target.value })
                  }
                  onBlur={() => setEditingField(null)}
                  onKeyDown={(e) => {
                    if (e.key === 'Escape') setEditingField(null)
                  }}
                  placeholder="(full content / the unfolding goes here)"
                />
              ) : (
                <div
                  className="node-body-display"
                  title="Double-click to edit"
                  onDoubleClick={() => setEditingField('body')}
                >
                  {selectedNode.data.body || (
                    <span className="placeholder-inline">
                      (double-click to add content)
                    </span>
                  )}
                </div>
              )}
            </>
          ) : (
            <p className="placeholder">Click a node to focus it.</p>
          )}
        </section>
        <section className="edges-pane">
          <h3>Potential moves</h3>
          {selectedNode == null ? (
            <p className="placeholder">No node focused.</p>
          ) : outgoingEdges.length === 0 ? (
            <p className="placeholder">No outgoing edges from this node.</p>
          ) : (
            <ul className="edge-list">
              {outgoingEdges.map((edge) => {
                const target = nodes.find((n) => n.id === edge.target)
                const targetLabel = target?.data.label || edge.target
                const edgeType = edge.data?.edgeType ?? 'supports'
                const label =
                  typeof edge.label === 'string' ? edge.label : ''
                const isSelected = edge.id === selectedEdgeId
                const isEditing = edge.id === editingEdgeId
                return (
                  <li
                    key={edge.id}
                    className={`edge-item${isSelected ? ' selected' : ''}${
                      isEditing ? ' editing' : ''
                    }`}
                    onClick={() => setSelectedEdgeId(edge.id)}
                    onDoubleClick={() => {
                      setSelectedEdgeId(edge.id)
                      setEditingEdgeId(edge.id)
                    }}
                  >
                    {isEditing ? (
                      <input
                        autoFocus
                        className="edge-label-input"
                        type="text"
                        value={label}
                        onChange={(e) =>
                          updateEdge(edge.id, { label: e.target.value })
                        }
                        onBlur={() => setEditingEdgeId(null)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') {
                            ;(e.target as HTMLInputElement).blur()
                          } else if (e.key === 'Escape') {
                            setEditingEdgeId(null)
                          }
                        }}
                        onClick={(e) => e.stopPropagation()}
                        placeholder={`→ ${targetLabel}`}
                      />
                    ) : (
                      <span className="edge-label-display">
                        {label || (
                          <span className="placeholder-inline">
                            → {targetLabel}
                          </span>
                        )}
                      </span>
                    )}
                    <select
                      className="edge-type-select"
                      value={edgeType}
                      onChange={(e) =>
                        updateEdge(edge.id, {
                          edgeType: e.target.value as EdgeType,
                        })
                      }
                    >
                      {EDGE_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                    <button
                      className="icon-button"
                      title={`Walk to ${targetLabel}`}
                      onClick={(e) => {
                        e.stopPropagation()
                        walkEdge(edge.id, edge.target)
                      }}
                    >
                      →
                    </button>
                    <button
                      className="icon-button danger"
                      title="Delete edge"
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteEdge(edge.id)
                      }}
                    >
                      ×
                    </button>
                  </li>
                )
              })}
            </ul>
          )}
        </section>
      </aside>
    </div>
  )
}

export default App
