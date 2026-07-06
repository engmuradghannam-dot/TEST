import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Bot, Brain, TrendingUp, Users, Package, Shield,
  Play, Pause, RotateCcw, Activity, Clock, CheckCircle,
  AlertTriangle, Zap, BarChart3, RefreshCw, Send
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const agentTypes = [
  {
    id: 'finance',
    name: 'Finance Agent',
    description: 'AI-powered financial analysis and automation',
    icon: TrendingUp,
    color: 'from-emerald-500 to-teal-600',
    bgColor: 'bg-emerald-50',
    capabilities: [
      'Invoice Classification',
      'Anomaly Detection',
      'Cash Flow Prediction',
      'Zakat Calculation',
      'Budget Variance Analysis'
    ],
    status: 'active',
    tasks_completed: 1247,
    accuracy: 94.5
  },
  {
    id: 'hr',
    name: 'HR Agent',
    description: 'Intelligent HR operations and workforce management',
    icon: Users,
    color: 'from-blue-500 to-indigo-600',
    bgColor: 'bg-blue-50',
    capabilities: [
      'Resume Screening',
      'Leave Optimization',
      'Performance Analysis',
      'Turnover Prediction',
      'Compliance Checking'
    ],
    status: 'active',
    tasks_completed: 892,
    accuracy: 91.2
  },
  {
    id: 'supply_chain',
    name: 'Supply Chain Agent',
    description: 'Smart inventory and procurement optimization',
    icon: Package,
    color: 'from-amber-500 to-orange-600',
    bgColor: 'bg-amber-50',
    capabilities: [
      'Demand Forecasting',
      'Inventory Optimization',
      'Auto Reorder',
      'Supplier Evaluation',
      'Lead Time Analysis'
    ],
    status: 'active',
    tasks_completed: 2156,
    accuracy: 88.7
  },
  {
    id: 'admin',
    name: 'Admin Agent',
    description: 'System monitoring and security management',
    icon: Shield,
    color: 'from-violet-500 to-purple-600',
    bgColor: 'bg-violet-50',
    capabilities: [
      'System Monitoring',
      'Security Audit',
      'Performance Tuning',
      'User Access Review',
      'Backup Verification'
    ],
    status: 'active',
    tasks_completed: 567,
    accuracy: 96.1
  }
];

export default function AgentDashboard() {
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [taskLogs, setTaskLogs] = useState([]);
  const [isRunning, setIsRunning] = useState(false);
  const [taskInput, setTaskInput] = useState('');

  const dispatchTask = async (agentType, action, parameters = {}) => {
    setIsRunning(true);
    try {
      const response = await axios.post('/api/ceos/ai/agents/dispatch/', {
        agent_type: agentType,
        action: action,
        parameters: {
          ...parameters,
          company_id: 'current',
          user_context: { role: 'Admin' }
        }
      });

      toast.success(`Task dispatched to ${agentType} agent`);
      setTaskLogs(prev => [{
        id: Date.now(),
        agent: agentType,
        action,
        result: response.data,
        timestamp: new Date().toISOString()
      }, ...prev]);
    } catch (error) {
      toast.error('Failed to dispatch task');
    } finally {
      setIsRunning(false);
    }
  };

  const broadcastTask = async (action, parameters = {}) => {
    setIsRunning(true);
    try {
      const response = await axios.post('/api/ceos/ai/agents/broadcast/', {
        action,
        parameters
      });

      toast.success('Broadcast task sent to all agents');
      Object.entries(response.data).forEach(([agent, result]) => {
        setTaskLogs(prev => [{
          id: Date.now() + Math.random(),
          agent,
          action,
          result,
          timestamp: new Date().toISOString()
        }, ...prev]);
      });
    } catch (error) {
      toast.error('Broadcast failed');
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center">
            <Brain className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">AI Agents Dashboard</h1>
            <p className="text-gray-500">Manage and monitor your AI workforce</p>
          </div>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {agentTypes.map((agent) => (
          <motion.div
            key={agent.id}
            whileHover={{ y: -4 }}
            className={`bg-white rounded-2xl shadow-sm border border-gray-200 p-5 cursor-pointer
              ${selectedAgent === agent.id ? 'ring-2 ring-indigo-500' : ''}`}
            onClick={() => setSelectedAgent(selectedAgent === agent.id ? null : agent.id)}
          >
            <div className="flex items-start justify-between mb-4">
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${agent.color} flex items-center justify-center`}>
                <agent.icon className="w-6 h-6 text-white" />
              </div>
              <div className={`px-2 py-1 rounded-full text-xs font-medium
                ${agent.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}`}>
                {agent.status}
              </div>
            </div>
            <h3 className="font-semibold text-gray-900 mb-1">{agent.name}</h3>
            <p className="text-sm text-gray-500 mb-4">{agent.description}</p>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">
                <CheckCircle className="w-4 h-4 inline mr-1" />
                {agent.tasks_completed.toLocaleString()} tasks
              </span>
              <span className="text-green-600 font-medium">
                {agent.accuracy}% accuracy
              </span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Task Dispatch Panel */}
      {selectedAgent && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-8"
        >
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">
              Dispatch Task to {agentTypes.find(a => a.id === selectedAgent)?.name}
            </h2>
            <button
              onClick={() => setSelectedAgent(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              Close
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
            {['analyze', 'predict', 'suggest', 'automate'].map((action) => (
              <button
                key={action}
                onClick={() => dispatchTask(selectedAgent, action)}
                disabled={isRunning}
                className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-xl text-sm font-medium text-gray-700 transition-colors disabled:opacity-50"
              >
                <Zap className="w-4 h-4" />
                {action.charAt(0).toUpperCase() + action.slice(1)}
              </button>
            ))}
          </div>

          <div className="flex gap-3">
            <input
              type="text"
              value={taskInput}
              onChange={(e) => setTaskInput(e.target.value)}
              placeholder="Enter custom task description..."
              className="flex-1 px-4 py-3 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            <button
              onClick={() => {
                dispatchTask(selectedAgent, 'analyze', { scenario: taskInput });
                setTaskInput('');
              }}
              disabled={isRunning || !taskInput.trim()}
              className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl text-sm font-medium hover:from-indigo-700 hover:to-violet-700 transition-all disabled:opacity-50"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </motion.div>
      )}

      {/* Broadcast Panel */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Broadcast to All Agents</h2>
          <button
            onClick={() => broadcastTask('analyze')}
            disabled={isRunning}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-lg text-sm hover:from-indigo-700 hover:to-violet-700 transition-all disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${isRunning ? 'animate-spin' : ''}`} />
            Run Full System Analysis
          </button>
        </div>
        <p className="text-sm text-gray-500">
          Dispatch analysis tasks to all agents simultaneously for comprehensive system overview.
        </p>
      </div>

      {/* Task Logs */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Agent Activity</h2>
        {taskLogs.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <Activity className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>No agent tasks have been dispatched yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {taskLogs.map((log) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-start gap-3 p-4 bg-gray-50 rounded-xl"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
                  ${log.result?.status === 'success' ? 'bg-green-100' : 'bg-red-100'}`}>
                  {log.result?.status === 'success' ? (
                    <CheckCircle className="w-4 h-4 text-green-600" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-red-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900 capitalize">{log.agent}</span>
                    <span className="text-xs text-gray-500">{log.action}</span>
                    <span className="text-xs text-gray-400">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 truncate">
                    {log.result?.summary || log.result?.analysis || JSON.stringify(log.result).substring(0, 100)}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
