import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain, TrendingUp, AlertTriangle, CheckCircle, XCircle,
  Clock, GitPullRequest, GitMerge, RotateCcw, Zap, BarChart3,
  ChevronRight, Shield, Activity, ArrowUpRight, Filter
} from 'lucide-react';
import api from '../lib/api';
import toast from 'react-hot-toast';

const mockImprovements = [
  {
    id: '1',
    title: 'Optimize Invoice Approval Workflow',
    description: 'The current invoice approval workflow has an average completion time of 4.2 hours. Analysis shows that parallelizing the manager and finance approval steps could reduce this to 1.8 hours.',
    type: 'workflow_optimization',
    status: 'suggested',
    expected_impact: 'Reduce approval time by 57% (saving ~120 hours/month)',
    risk: 'low',
    confidence: 0.89,
    created_at: '2026-07-05T10:30:00Z',
    implementation_steps: [
      'Modify workflow definition to add parallel gateway',
      'Update state machine rules for concurrent approvals',
      'Add notification handlers for parallel completion',
      'Test with sample invoices',
      'Deploy to production'
    ]
  },
  {
    id: '2',
    title: 'Add Auto-Reorder for Low Stock Items',
    description: 'AI analysis detected that 23 inventory items frequently run below minimum stock levels. Implementing automatic purchase order generation could prevent stockouts.',
    type: 'automation_addition',
    status: 'pending_approval',
    expected_impact: 'Reduce stockouts by 78%, improve customer satisfaction',
    risk: 'medium',
    confidence: 0.82,
    created_at: '2026-07-04T14:20:00Z',
    implementation_steps: [
      'Create inventory monitoring scheduled task',
      'Build auto-reorder logic with supplier preferences',
      'Add approval workflow for auto-generated POs',
      'Configure notification rules',
      'Enable for pilot warehouse'
    ]
  },
  {
    id: '3',
    title: 'Database Index Optimization',
    description: 'Query analysis shows that invoice list queries are taking 2.3s on average. Adding composite indexes on (company_id, status, created_at) could reduce to <200ms.',
    type: 'performance_tuning',
    status: 'approved',
    expected_impact: 'Reduce query time by 91%, improve UX',
    risk: 'low',
    confidence: 0.95,
    created_at: '2026-07-03T09:15:00Z',
    implementation_steps: [
      'Create migration for new indexes',
      'Run EXPLAIN ANALYZE to verify',
      'Monitor query performance post-deployment',
      'Rollback plan: drop indexes if issues arise'
    ]
  },
  {
    id: '4',
    title: 'Enhance AI Invoice Classification',
    description: 'Current auto-classification accuracy is 88%. Retraining with additional vendor data could improve to 95%+.',
    type: 'rule_adjustment',
    status: 'deployed',
    expected_impact: 'Improve classification accuracy by 7%',
    risk: 'low',
    confidence: 0.91,
    created_at: '2026-07-01T11:00:00Z',
    implementation_steps: [
      'Collect additional training data',
      'Fine-tune classification model',
      'A/B test against current model',
      'Deploy if accuracy > 93%'
    ]
  }
];

const statusColors = {
  detected: 'bg-gray-100 text-gray-700',
  analyzing: 'bg-blue-100 text-blue-700',
  suggested: 'bg-amber-100 text-amber-700',
  pending_approval: 'bg-orange-100 text-orange-700',
  approved: 'bg-green-100 text-green-700',
  deployed: 'bg-indigo-100 text-indigo-700',
  rolled_back: 'bg-red-100 text-red-700',
  rejected: 'bg-gray-100 text-gray-500'
};

const typeIcons = {
  workflow_optimization: GitMerge,
  rule_adjustment: Shield,
  automation_addition: Zap,
  ui_enhancement: Activity,
  performance_tuning: TrendingUp,
  security_hardening: Shield,
  data_quality: BarChart3
};

export default function SelfImprovementDashboard() {
  const [improvements, setImprovements] = useState(mockImprovements);
  const [selectedImprovement, setSelectedImprovement] = useState(null);
  const [filter, setFilter] = useState('all');
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  const filtered = filter === 'all'
    ? improvements
    : improvements.filter(i => i.status === filter);

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    try {
      const response = await api.post('/core/system/improvements/analyze_system/');
      toast.success('System analysis completed');
      // Would refresh improvements list
    } catch (error) {
      toast.error('Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const approveImprovement = async (id) => {
    try {
      await api.post(`/core/system/improvements/${id}/approve/`);
      setImprovements(prev => prev.map(i => i.id === id ? { ...i, status: 'approved' } : i));
      toast.success('Improvement approved');
    } catch (error) {
      toast.error('Approval failed');
    }
  };

  const deployImprovement = async (id) => {
    try {
      await api.post(`/core/system/improvements/${id}/deploy/`);
      setImprovements(prev => prev.map(i => i.id === id ? { ...i, status: 'deployed' } : i));
      toast.success('Improvement deployed');
    } catch (error) {
      toast.error('Deployment failed');
    }
  };

  const rollbackImprovement = async (id) => {
    try {
      await api.post(`/core/system/improvements/${id}/rollback/`);
      setImprovements(prev => prev.map(i => i.id === id ? { ...i, status: 'rolled_back' } : i));
      toast.success('Improvement rolled back');
    } catch (error) {
      toast.error('Rollback failed');
    }
  };

  const stats = {
    total: improvements.length,
    pending: improvements.filter(i => ['detected', 'suggested', 'pending_approval'].includes(i.status)).length,
    deployed: improvements.filter(i => i.status === 'deployed').length,
    rolled_back: improvements.filter(i => i.status === 'rolled_back').length
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Self-Improvement Center</h1>
              <p className="text-gray-500">AI-powered system optimization and evolution</p>
            </div>
          </div>
          <button
            onClick={runAnalysis}
            disabled={isAnalyzing}
            className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl hover:from-indigo-700 hover:to-violet-700 transition-all disabled:opacity-50"
          >
            <Activity className={`w-4 h-4 ${isAnalyzing ? 'animate-spin' : ''}`} />
            {isAnalyzing ? 'Analyzing...' : 'Run System Analysis'}
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
          <div className="text-3xl font-bold text-gray-900">{stats.total}</div>
          <div className="text-sm text-gray-500 mt-1">Total Improvements</div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
          <div className="text-3xl font-bold text-amber-600">{stats.pending}</div>
          <div className="text-sm text-gray-500 mt-1">Pending Review</div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
          <div className="text-3xl font-bold text-green-600">{stats.deployed}</div>
          <div className="text-sm text-gray-500 mt-1">Deployed</div>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-5">
          <div className="text-3xl font-bold text-red-600">{stats.rolled_back}</div>
          <div className="text-sm text-gray-500 mt-1">Rolled Back</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
        {['all', 'suggested', 'pending_approval', 'approved', 'deployed', 'rolled_back'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all
              ${filter === status
                ? 'bg-indigo-600 text-white'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
              }`}
          >
            {status.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Improvements List */}
      <div className="space-y-4">
        {filtered.map((improvement) => {
          const TypeIcon = typeIcons[improvement.type] || Zap;
          return (
            <motion.div
              key={improvement.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-2xl shadow-sm border border-gray-200 p-6 cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedImprovement(improvement)}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-4">
                  <div className="w-10 h-10 bg-gradient-to-br from-violet-100 to-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <TypeIcon className="w-5 h-5 text-indigo-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 mb-1">{improvement.title}</h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{improvement.description}</p>
                    <div className="flex items-center gap-3 mt-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[improvement.status]}`}>
                        {improvement.status.replace('_', ' ')}
                      </span>
                      <span className="text-xs text-gray-500">
                        Confidence: {Math.round(improvement.confidence * 100)}%
                      </span>
                      <span className="text-xs text-gray-500">
                        Risk: {improvement.risk}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {improvement.status === 'suggested' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        approveImprovement(improvement.id);
                      }}
                      className="px-3 py-1.5 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition-colors"
                    >
                      Approve
                    </button>
                  )}
                  {improvement.status === 'approved' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        deployImprovement(improvement.id);
                      }}
                      className="px-3 py-1.5 bg-indigo-100 text-indigo-700 rounded-lg text-sm font-medium hover:bg-indigo-200 transition-colors"
                    >
                      Deploy
                    </button>
                  )}
                  {improvement.status === 'deployed' && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        rollbackImprovement(improvement.id);
                      }}
                      className="px-3 py-1.5 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
                    >
                      Rollback
                    </button>
                  )}
                  <ChevronRight className="w-5 h-5 text-gray-400" />
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Detail Modal */}
      <AnimatePresence>
        {selectedImprovement && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold text-gray-900">{selectedImprovement.title}</h2>
                    <p className="text-gray-500 mt-1">{selectedImprovement.description}</p>
                  </div>
                  <button
                    onClick={() => setSelectedImprovement(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <XCircle className="w-6 h-6" />
                  </button>
                </div>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-500 mb-1">Expected Impact</div>
                    <div className="text-sm font-medium text-gray-900">{selectedImprovement.expected_impact}</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-500 mb-1">Risk Level</div>
                    <div className={`text-sm font-medium capitalize
                      ${selectedImprovement.risk === 'low' ? 'text-green-600' :
                        selectedImprovement.risk === 'medium' ? 'text-amber-600' : 'text-red-600'}`}>
                      {selectedImprovement.risk}
                    </div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4">
                    <div className="text-sm text-gray-500 mb-1">AI Confidence</div>
                    <div className="text-sm font-medium text-indigo-600">
                      {Math.round(selectedImprovement.confidence * 100)}%
                    </div>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-3">Implementation Steps</h3>
                  <div className="space-y-2">
                    {selectedImprovement.implementation_steps.map((step, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <div className="w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-xs font-medium flex-shrink-0">
                          {i + 1}
                        </div>
                        <p className="text-sm text-gray-700">{step}</p>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3">
                  {selectedImprovement.status === 'suggested' && (
                    <button
                      onClick={() => {
                        approveImprovement(selectedImprovement.id);
                        setSelectedImprovement(null);
                      }}
                      className="flex-1 py-3 bg-green-600 text-white rounded-xl font-medium hover:bg-green-700 transition-colors"
                    >
                      Approve for Deployment
                    </button>
                  )}
                  {selectedImprovement.status === 'approved' && (
                    <button
                      onClick={() => {
                        deployImprovement(selectedImprovement.id);
                        setSelectedImprovement(null);
                      }}
                      className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors"
                    >
                      Deploy Now
                    </button>
                  )}
                  {selectedImprovement.status === 'deployed' && (
                    <button
                      onClick={() => {
                        rollbackImprovement(selectedImprovement.id);
                        setSelectedImprovement(null);
                      }}
                      className="flex-1 py-3 bg-red-100 text-red-700 rounded-xl font-medium hover:bg-red-200 transition-colors"
                    >
                      Rollback
                    </button>
                  )}
                  <button
                    onClick={() => setSelectedImprovement(null)}
                    className="px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-medium hover:bg-gray-200 transition-colors"
                  >
                    Close
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
