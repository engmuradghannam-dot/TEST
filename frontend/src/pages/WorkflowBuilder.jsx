import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge,
  Panel,
  NodeToolbar,
  NodeResizer,
  useReactFlow,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Play, Square, Save, Download, Upload, Trash2, Plus,
  Settings, GitBranch, User, Zap, Database, FileText,
  CheckCircle, XCircle, AlertTriangle, ChevronRight,
  MessageSquare, Bot, Workflow, RefreshCw, Copy
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import toast from 'react-hot-toast';
import axios from 'axios';

// Node Types
const nodeTypes = {
  startEvent: StartEventNode,
  endEvent: EndEventNode,
  task: TaskNode,
  userTask: UserTaskNode,
  serviceTask: ServiceTaskNode,
  scriptTask: ScriptTaskNode,
  sendTask: SendTaskNode,
  receiveTask: ReceiveTaskNode,
  businessRuleTask: BusinessRuleTaskNode,
  exclusiveGateway: ExclusiveGatewayNode,
  parallelGateway: ParallelGatewayNode,
  inclusiveGateway: InclusiveGatewayNode,
  subProcess: SubProcessNode,
  callActivity: CallActivityNode,
  boundaryEvent: BoundaryEventNode,
};

// Custom Node Components
function StartEventNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-12 h-12 rounded-full border-4 flex items-center justify-center
        ${selected ? 'border-green-500 bg-green-50' : 'border-green-600 bg-white'}`}>
        <Play className="w-5 h-5 text-green-600" />
      </div>
      <NodeToolbar isVisible={selected} position={Position.Top}>
        <button className="bg-red-500 text-white px-2 py-1 rounded text-xs">Delete</button>
      </NodeToolbar>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-gray-600 whitespace-nowrap">
        {data.label || 'Start'}
      </div>
    </div>
  );
}

function EndEventNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-12 h-12 rounded-full border-4 flex items-center justify-center
        ${selected ? 'border-red-500 bg-red-50' : 'border-red-600 bg-white'}`}>
        <Square className="w-5 h-5 text-red-600" />
      </div>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-gray-600 whitespace-nowrap">
        {data.label || 'End'}
      </div>
    </div>
  );
}

function TaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white'}`}>
      <div className="flex items-center gap-2">
        <FileText className="w-4 h-4 text-blue-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Task'}</span>
      </div>
      {data.description && (
        <p className="text-xs text-gray-500 mt-1">{data.description}</p>
      )}
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function UserTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-indigo-500 bg-indigo-50' : 'border-indigo-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <User className="w-4 h-4 text-indigo-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'User Task'}</span>
      </div>
      {data.assignee && (
        <p className="text-xs text-gray-500 mt-1">Assignee: {data.assignee}</p>
      )}
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function ServiceTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-amber-500 bg-amber-50' : 'border-amber-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Zap className="w-4 h-4 text-amber-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Service'}</span>
      </div>
      {data.service && (
        <p className="text-xs text-gray-500 mt-1">{data.service}</p>
      )}
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function ScriptTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-purple-500 bg-purple-50' : 'border-purple-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Code className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Script'}</span>
      </div>
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function SendTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-cyan-500 bg-cyan-50' : 'border-cyan-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Send className="w-4 h-4 text-cyan-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Send'}</span>
      </div>
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function ReceiveTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-teal-500 bg-teal-50' : 'border-teal-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Inbox className="w-4 h-4 text-teal-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Receive'}</span>
      </div>
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function BusinessRuleTaskNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-orange-500 bg-orange-50' : 'border-orange-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Scale className="w-4 h-4 text-orange-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Business Rule'}</span>
      </div>
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function ExclusiveGatewayNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-14 h-14 rotate-45 border-2 flex items-center justify-center
        ${selected ? 'border-yellow-500 bg-yellow-50' : 'border-yellow-600 bg-white'}`}>
        <GitBranch className="w-5 h-5 text-yellow-600 -rotate-45" />
      </div>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-gray-600 whitespace-nowrap">
        {data.label || 'XOR'}
      </div>
    </div>
  );
}

function ParallelGatewayNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-14 h-14 rotate-45 border-2 flex items-center justify-center
        ${selected ? 'border-emerald-500 bg-emerald-50' : 'border-emerald-600 bg-white'}`}>
        <Plus className="w-5 h-5 text-emerald-600 -rotate-45" />
      </div>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-gray-600 whitespace-nowrap">
        {data.label || 'AND'}
      </div>
    </div>
  );
}

function InclusiveGatewayNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-14 h-14 rotate-45 border-2 flex items-center justify-center
        ${selected ? 'border-pink-500 bg-pink-50' : 'border-pink-600 bg-white'}`}>
        <Circle className="w-5 h-5 text-pink-600 -rotate-45" />
      </div>
      <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 text-xs font-medium text-gray-600 whitespace-nowrap">
        {data.label || 'OR'}
      </div>
    </div>
  );
}

function SubProcessNode({ data, selected }) {
  return (
    <div className={`relative min-w-[160px] min-h-[100px] rounded-lg border-2 p-3 shadow-sm
      ${selected ? 'border-violet-500 bg-violet-50' : 'border-violet-400 bg-white'}`}>
      <div className="flex items-center gap-2 border-b border-violet-200 pb-2 mb-2">
        <Workflow className="w-4 h-4 text-violet-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Sub-Process'}</span>
      </div>
      <div className="text-xs text-gray-500">Double-click to edit</div>
      <NodeResizer isVisible={selected} minWidth={160} minHeight={100} />
    </div>
  );
}

function CallActivityNode({ data, selected }) {
  return (
    <div className={`relative min-w-[140px] rounded-lg border-2 border-dashed p-3 shadow-sm
      ${selected ? 'border-violet-500 bg-violet-50' : 'border-violet-400 bg-white'}`}>
      <div className="flex items-center gap-2">
        <Phone className="w-4 h-4 text-violet-600" />
        <span className="text-sm font-medium text-gray-800">{data.label || 'Call Activity'}</span>
      </div>
      <NodeResizer isVisible={selected} minWidth={140} minHeight={60} />
    </div>
  );
}

function BoundaryEventNode({ data, selected }) {
  return (
    <div className="relative">
      <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center
        ${selected ? 'border-red-400 bg-red-50' : 'border-red-500 bg-white'}`}>
        <AlertTriangle className="w-4 h-4 text-red-500" />
      </div>
    </div>
  );
}

// Node Palette
const nodePalette = [
  { type: 'startEvent', label: 'Start', icon: Play, color: 'green' },
  { type: 'endEvent', label: 'End', icon: Square, color: 'red' },
  { type: 'task', label: 'Task', icon: FileText, color: 'blue' },
  { type: 'userTask', label: 'User Task', icon: User, color: 'indigo' },
  { type: 'serviceTask', label: 'Service', icon: Zap, color: 'amber' },
  { type: 'scriptTask', label: 'Script', icon: Code, color: 'purple' },
  { type: 'sendTask', label: 'Send', icon: Send, color: 'cyan' },
  { type: 'receiveTask', label: 'Receive', icon: Inbox, color: 'teal' },
  { type: 'businessRuleTask', label: 'Business Rule', icon: Scale, color: 'orange' },
  { type: 'exclusiveGateway', label: 'XOR Gateway', icon: GitBranch, color: 'yellow' },
  { type: 'parallelGateway', label: 'AND Gateway', icon: Plus, color: 'emerald' },
  { type: 'inclusiveGateway', label: 'OR Gateway', icon: Circle, color: 'pink' },
  { type: 'subProcess', label: 'Sub-Process', icon: Workflow, color: 'violet' },
  { type: 'callActivity', label: 'Call Activity', icon: Phone, color: 'violet' },
];

// Main Component
export default function VisualWorkflowBuilder() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [selectedEdge, setSelectedEdge] = useState(null);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [workflowDescription, setWorkflowDescription] = useState('');
  const [showAIGenerator, setShowAIGenerator] = useState(false);
  const [aiPrompt, setAiPrompt] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [showProperties, setShowProperties] = useState(false);
  const [nodeProperties, setNodeProperties] = useState({});
  const reactFlowWrapper = useRef(null);
  const { project, fitView } = useReactFlow();

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({
      ...params,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#6366f1', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' }
    }, eds)),
    [setEdges]
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const position = project({
        x: event.clientX - reactFlowWrapper.current.getBoundingClientRect().left,
        y: event.clientY - reactFlowWrapper.current.getBoundingClientRect().top,
      });

      const newNode = {
        id: `${type}_${Date.now()}`,
        type,
        position,
        data: { label: `${type} node` },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [project, setNodes]
  );

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
    setSelectedEdge(null);
    setShowProperties(true);
    setNodeProperties(node.data || {});
  }, []);

  const onEdgeClick = useCallback((event, edge) => {
    setSelectedEdge(edge);
    setSelectedNode(null);
    setShowProperties(true);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    setSelectedEdge(null);
    setShowProperties(false);
  }, []);

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const deleteSelected = () => {
    if (selectedNode) {
      setNodes((nds) => nds.filter((n) => n.id !== selectedNode.id));
      setEdges((eds) => eds.filter((e) => e.source !== selectedNode.id && e.target !== selectedNode.id));
      setSelectedNode(null);
      toast.success('Node deleted');
    }
    if (selectedEdge) {
      setEdges((eds) => eds.filter((e) => e.id !== selectedEdge.id));
      setSelectedEdge(null);
      toast.success('Edge deleted');
    }
  };

  const saveWorkflow = async () => {
    try {
      const workflowData = {
        name: workflowName,
        description: workflowDescription,
        nodes: nodes.map(n => ({
          id: n.id,
          type: n.type,
          position: n.position,
          data: n.data,
          width: n.width,
          height: n.height
        })),
        edges: edges.map(e => ({
          id: e.id,
          source: e.source,
          target: e.target,
          label: e.label,
          condition: e.data?.condition || ''
        }))
      };

      await axios.post('/api/ceos/workflows/definitions/', workflowData);
      toast.success('Workflow saved successfully');
    } catch (error) {
      toast.error('Failed to save workflow');
      console.error(error);
    }
  };

  const exportWorkflow = () => {
    const workflowData = {
      name: workflowName,
      description: workflowDescription,
      nodes,
      edges
    };
    const blob = new Blob([JSON.stringify(workflowData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${workflowName.replace(/\s+/g, '_').toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success('Workflow exported');
  };

  const importWorkflow = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target.result);
        setWorkflowName(data.name || 'Imported Workflow');
        setWorkflowDescription(data.description || '');
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
        toast.success('Workflow imported');
      } catch (err) {
        toast.error('Invalid workflow file');
      }
    };
    reader.readAsText(file);
  };

  const generateWithAI = async () => {
    if (!aiPrompt.trim()) {
      toast.error('Please enter a description');
      return;
    }

    setIsGenerating(true);
    try {
      const response = await axios.post('/api/ceos/ai/workflow-generator/generate/', {
        description: aiPrompt
      });

      const data = response.data;
      if (data.nodes && data.edges) {
        setNodes(data.nodes.map(n => ({
          ...n,
          position: { x: n.x || 0, y: n.y || 0 }
        })));
        setEdges(data.edges.map(e => ({
          ...e,
          type: 'smoothstep',
          animated: true,
          style: { stroke: '#6366f1', strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' }
        })));
        setWorkflowName(data.name || 'AI Generated Workflow');
        toast.success('Workflow generated by AI');
        setShowAIGenerator(false);
      }
    } catch (error) {
      toast.error('AI generation failed');
      console.error(error);
    } finally {
      setIsGenerating(false);
    }
  };

  const updateNodeProperties = () => {
    if (!selectedNode) return;
    setNodes((nds) =>
      nds.map((n) =>
        n.id === selectedNode.id
          ? { ...n, data: { ...n.data, ...nodeProperties } }
          : n
      )
    );
    toast.success('Properties updated');
  };

  const validateWorkflow = () => {
    const startNodes = nodes.filter(n => n.type === 'startEvent');
    const endNodes = nodes.filter(n => n.type === 'endEvent');
    const errors = [];

    if (startNodes.length === 0) errors.push('Missing start event');
    if (startNodes.length > 1) errors.push('Multiple start events');
    if (endNodes.length === 0) errors.push('Missing end event');

    // Check for disconnected nodes
    const connectedIds = new Set();
    edges.forEach(e => {
      connectedIds.add(e.source);
      connectedIds.add(e.target);
    });
    startNodes.forEach(n => connectedIds.add(n.id));

    nodes.forEach(n => {
      if (!connectedIds.has(n.id)) {
        errors.push(`Node "${n.data.label || n.id}" is disconnected`);
      }
    });

    if (errors.length === 0) {
      toast.success('Workflow is valid');
    } else {
      errors.forEach(err => toast.error(err));
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Workflow className="w-6 h-6 text-indigo-600" />
          <div>
            <input
              type="text"
              value={workflowName}
              onChange={(e) => setWorkflowName(e.target.value)}
              className="text-lg font-semibold text-gray-900 bg-transparent border-none focus:outline-none focus:ring-0"
            />
            <input
              type="text"
              value={workflowDescription}
              onChange={(e) => setWorkflowDescription(e.target.value)}
              placeholder="Description..."
              className="text-sm text-gray-500 bg-transparent border-none focus:outline-none focus:ring-0 block"
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowAIGenerator(true)}
            className="flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-lg hover:from-violet-700 hover:to-indigo-700 transition-all"
          >
            <Bot className="w-4 h-4" />
            AI Generate
          </button>
          <button
            onClick={validateWorkflow}
            className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all"
          >
            <CheckCircle className="w-4 h-4" />
            Validate
          </button>
          <button
            onClick={saveWorkflow}
            className="flex items-center gap-2 px-3 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-all"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
          <button
            onClick={exportWorkflow}
            className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all"
          >
            <Download className="w-4 h-4" />
            Export
          </button>
          <label className="flex items-center gap-2 px-3 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input type="file" accept=".json" onChange={importWorkflow} className="hidden" />
          </label>
          {(selectedNode || selectedEdge) && (
            <button
              onClick={deleteSelected}
              className="flex items-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-all"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          )}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Node Palette */}
        <div className="w-64 bg-white border-r border-gray-200 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Node Palette</h3>
            <div className="space-y-2">
              {nodePalette.map((node) => (
                <div
                  key={node.type}
                  draggable
                  onDragStart={(e) => onDragStart(e, node.type)}
                  className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 cursor-move border border-transparent hover:border-gray-200 transition-all"
                >
                  <node.icon className={`w-4 h-4 text-${node.color}-600`} />
                  <span className="text-sm text-gray-700">{node.label}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="flex-1" ref={reactFlowWrapper}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            fitView
            attributionPosition="bottom-left"
          >
            <Background color="#e5e7eb" gap={16} size={1} />
            <Controls />
            <MiniMap
              nodeStrokeWidth={3}
              zoomable
              pannable
              className="bg-white rounded-lg shadow-lg"
            />
            <Panel position="top-right">
              <div className="bg-white rounded-lg shadow-lg p-2 text-xs text-gray-500">
                {nodes.length} nodes | {edges.length} edges
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Properties Panel */}
        <AnimatePresence>
          {showProperties && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="bg-white border-l border-gray-200 overflow-y-auto"
            >
              <div className="p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold text-gray-900">
                    {selectedNode ? 'Node Properties' : selectedEdge ? 'Edge Properties' : 'Properties'}
                  </h3>
                  <button onClick={() => setShowProperties(false)} className="text-gray-400 hover:text-gray-600">
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {selectedNode && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Label</label>
                      <input
                        type="text"
                        value={nodeProperties.label || ''}
                        onChange={(e) => setNodeProperties({ ...nodeProperties, label: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
                      <textarea
                        value={nodeProperties.description || ''}
                        onChange={(e) => setNodeProperties({ ...nodeProperties, description: e.target.value })}
                        rows={3}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    {selectedNode.type === 'userTask' && (
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Assignee Role</label>
                        <select
                          value={nodeProperties.assigneeRole || ''}
                          onChange={(e) => setNodeProperties({ ...nodeProperties, assigneeRole: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        >
                          <option value="">Select Role</option>
                          <option value="Admin">Admin</option>
                          <option value="Manager">Manager</option>
                          <option value="Accountant">Accountant</option>
                          <option value="User">User</option>
                        </select>
                      </div>
                    )}
                    {selectedNode.type === 'serviceTask' && (
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Service Name</label>
                        <input
                          type="text"
                          value={nodeProperties.service || ''}
                          onChange={(e) => setNodeProperties({ ...nodeProperties, service: e.target.value })}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                    )}
                    {selectedNode.type === 'scriptTask' && (
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">Script</label>
                        <textarea
                          value={nodeProperties.script || ''}
                          onChange={(e) => setNodeProperties({ ...nodeProperties, script: e.target.value })}
                          rows={5}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                        />
                      </div>
                    )}
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Due Hours</label>
                      <input
                        type="number"
                        value={nodeProperties.dueHours || ''}
                        onChange={(e) => setNodeProperties({ ...nodeProperties, dueHours: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <button
                      onClick={updateNodeProperties}
                      className="w-full py-2 bg-indigo-600 text-white rounded-lg text-sm hover:bg-indigo-700 transition-all"
                    >
                      Update Properties
                    </button>
                  </div>
                )}

                {selectedEdge && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Condition</label>
                      <input
                        type="text"
                        value={selectedEdge.data?.condition || ''}
                        onChange={(e) => {
                          setEdges((eds) =>
                            eds.map((ed) =>
                              ed.id === selectedEdge.id
                                ? { ...ed, data: { ...ed.data, condition: e.target.value } }
                                : ed
                            )
                          );
                        }}
                        placeholder="e.g., amount > 10000"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Label</label>
                      <input
                        type="text"
                        value={selectedEdge.label || ''}
                        onChange={(e) => {
                          setEdges((eds) =>
                            eds.map((ed) =>
                              ed.id === selectedEdge.id
                                ? { ...ed, label: e.target.value }
                                : ed
                            )
                          );
                        }}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* AI Generator Modal */}
      <AnimatePresence>
        {showAIGenerator && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 overflow-hidden"
            >
              <div className="bg-gradient-to-r from-violet-600 to-indigo-600 px-6 py-4">
                <div className="flex items-center gap-3">
                  <Bot className="w-6 h-6 text-white" />
                  <h2 className="text-lg font-semibold text-white">AI Workflow Generator</h2>
                </div>
                <p className="text-violet-100 text-sm mt-1">
                  Describe your business process in natural language and let AI generate the workflow
                </p>
              </div>
              <div className="p-6">
                <textarea
                  value={aiPrompt}
                  onChange={(e) => setAiPrompt(e.target.value)}
                  placeholder="Example: Any invoice above 10,000 SAR needs manager approval, then finance approval, then automatic email notification to the customer..."
                  rows={5}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-violet-500 focus:border-violet-500 resize-none"
                />
                <div className="flex items-center gap-2 mt-4">
                  <button
                    onClick={generateWithAI}
                    disabled={isGenerating}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-lg hover:from-violet-700 hover:to-indigo-700 transition-all disabled:opacity-50"
                  >
                    {isGenerating ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Bot className="w-4 h-4" />
                    )}
                    {isGenerating ? 'Generating...' : 'Generate Workflow'}
                  </button>
                  <button
                    onClick={() => setShowAIGenerator(false)}
                    className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// Missing imports
import { Position, Code, Send, Inbox, Scale, Circle, Phone } from 'lucide-react';
