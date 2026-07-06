import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Puzzle, Star, Download, Shield, CheckCircle, X,
  Search, Filter, Grid, List, ChevronRight, Tag,
  DollarSign, Users, Clock, ArrowUpRight, Package
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

const categories = [
  { id: 'all', name: 'All Plugins', icon: Puzzle },
  { id: 'finance', name: 'Finance', icon: DollarSign },
  { id: 'hr', name: 'HR & Payroll', icon: Users },
  { id: 'inventory', name: 'Inventory', icon: Package },
  { id: 'crm', name: 'CRM', icon: Users },
  { id: 'analytics', name: 'Analytics', icon: ArrowUpRight },
  { id: 'automation', name: 'Automation', icon: Clock },
];

const mockPlugins = [
  {
    id: '1',
    name: 'Advanced Zakat Calculator',
    description: 'Automated Zakat calculation with Saudi regulatory compliance',
    category: 'finance',
    author: 'Nexus Team',
    version: '2.1.0',
    rating: 4.8,
    review_count: 124,
    download_count: 3456,
    is_premium: true,
    price: 49.99,
    tags: ['zakat', 'tax', 'compliance'],
    icon: '💰',
    status: 'not_installed'
  },
  {
    id: '2',
    name: 'AI Invoice Scanner',
    description: 'OCR-powered invoice scanning with automatic data extraction',
    category: 'finance',
    author: 'AI Labs',
    version: '1.5.0',
    rating: 4.6,
    review_count: 89,
    download_count: 2134,
    is_premium: false,
    price: 0,
    tags: ['ocr', 'ai', 'invoice'],
    icon: '📄',
    status: 'installed'
  },
  {
    id: '3',
    name: 'Employee Attendance AI',
    description: 'Facial recognition attendance with anomaly detection',
    category: 'hr',
    author: 'Vision Tech',
    version: '3.0.0',
    rating: 4.9,
    review_count: 256,
    download_count: 5678,
    is_premium: true,
    price: 99.99,
    tags: ['attendance', 'ai', 'facial-recognition'],
    icon: '👤',
    status: 'not_installed'
  },
  {
    id: '4',
    name: 'Smart Inventory Forecast',
    description: 'ML-powered demand forecasting for inventory optimization',
    category: 'inventory',
    author: 'DataMind',
    version: '1.2.0',
    rating: 4.5,
    review_count: 67,
    download_count: 1234,
    is_premium: true,
    price: 79.99,
    tags: ['ml', 'forecasting', 'inventory'],
    icon: '📦',
    status: 'not_installed'
  },
  {
    id: '5',
    name: 'Customer Sentiment Analysis',
    description: 'Real-time sentiment analysis for customer interactions',
    category: 'crm',
    author: 'NLP Solutions',
    version: '2.0.0',
    rating: 4.7,
    review_count: 145,
    download_count: 2890,
    is_premium: false,
    price: 0,
    tags: ['nlp', 'sentiment', 'crm'],
    icon: '💬',
    status: 'installed'
  },
  {
    id: '6',
    name: 'Advanced BI Dashboard',
    description: 'Interactive business intelligence with predictive analytics',
    category: 'analytics',
    author: 'Nexus Team',
    version: '4.0.0',
    rating: 4.9,
    review_count: 312,
    download_count: 8901,
    is_premium: true,
    price: 149.99,
    tags: ['bi', 'analytics', 'dashboard'],
    icon: '📊',
    status: 'not_installed'
  }
];

export default function PluginMarketplace() {
  const [plugins, setPlugins] = useState(mockPlugins);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewMode, setViewMode] = useState('grid');
  const [selectedPlugin, setSelectedPlugin] = useState(null);
  const [isInstalling, setIsInstalling] = useState(false);
  const [installedPlugins, setInstalledPlugins] = useState(
    mockPlugins.filter(p => p.status === 'installed').map(p => p.id)
  );

  const filteredPlugins = plugins.filter(plugin => {
    const matchesCategory = selectedCategory === 'all' || plugin.category === selectedCategory;
    const matchesSearch = plugin.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         plugin.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         plugin.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  const installPlugin = async (plugin) => {
    setIsInstalling(true);
    try {
      await axios.post(`/api/ceos/plugins/registry/${plugin.id}/install/`);
      setInstalledPlugins(prev => [...prev, plugin.id]);
      toast.success(`${plugin.name} installed successfully`);
    } catch (error) {
      toast.error('Installation failed');
    } finally {
      setIsInstalling(false);
    }
  };

  const uninstallPlugin = async (plugin) => {
    try {
      // Would call uninstall API
      setInstalledPlugins(prev => prev.filter(id => id !== plugin.id));
      toast.success(`${plugin.name} uninstalled`);
    } catch (error) {
      toast.error('Uninstall failed');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-600 to-indigo-600 rounded-xl flex items-center justify-center">
            <Puzzle className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Plugin Marketplace</h1>
            <p className="text-gray-500">Extend your ERP with powerful plugins</p>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search plugins..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2.5 rounded-xl transition-colors ${viewMode === 'grid' ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-600'}`}
            >
              <Grid className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2.5 rounded-xl transition-colors ${viewMode === 'list' ? 'bg-indigo-100 text-indigo-600' : 'bg-gray-100 text-gray-600'}`}
            >
              <List className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto pb-4 mb-6">
        {categories.map((cat) => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(cat.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all
              ${selectedCategory === cat.id
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-200'
              }`}
          >
            <cat.icon className="w-4 h-4" />
            {cat.name}
          </button>
        ))}
      </div>

      {/* Plugins Grid/List */}
      {viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPlugins.map((plugin) => (
            <motion.div
              key={plugin.id}
              whileHover={{ y: -4 }}
              className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
              onClick={() => setSelectedPlugin(plugin)}
            >
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="text-4xl">{plugin.icon}</div>
                  {plugin.is_premium && (
                    <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-medium">
                      Premium
                    </span>
                  )}
                </div>
                <h3 className="font-semibold text-gray-900 mb-2">{plugin.name}</h3>
                <p className="text-sm text-gray-500 mb-4 line-clamp-2">{plugin.description}</p>
                <div className="flex items-center gap-4 text-sm text-gray-500 mb-4">
                  <span className="flex items-center gap-1">
                    <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                    {plugin.rating}
                  </span>
                  <span>({plugin.review_count})</span>
                  <span className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    {plugin.download_count.toLocaleString()}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex gap-1">
                    {plugin.tags.slice(0, 2).map((tag) => (
                      <span key={tag} className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                        {tag}
                      </span>
                    ))}
                  </div>
                  {installedPlugins.includes(plugin.id) ? (
                    <span className="flex items-center gap-1 text-green-600 text-sm font-medium">
                      <CheckCircle className="w-4 h-4" />
                      Installed
                    </span>
                  ) : (
                    <span className="text-indigo-600 font-medium">
                      {plugin.price > 0 ? `$${plugin.price}` : 'Free'}
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
          {filteredPlugins.map((plugin) => (
            <div
              key={plugin.id}
              className="flex items-center gap-4 p-4 border-b border-gray-100 last:border-0 hover:bg-gray-50 cursor-pointer"
              onClick={() => setSelectedPlugin(plugin)}
            >
              <div className="text-3xl">{plugin.icon}</div>
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{plugin.name}</h3>
                <p className="text-sm text-gray-500">{plugin.description}</p>
              </div>
              <div className="flex items-center gap-4">
                <span className="flex items-center gap-1 text-sm text-gray-500">
                  <Star className="w-4 h-4 text-amber-400 fill-amber-400" />
                  {plugin.rating}
                </span>
                {installedPlugins.includes(plugin.id) ? (
                  <span className="flex items-center gap-1 text-green-600 text-sm">
                    <CheckCircle className="w-4 h-4" />
                    Installed
                  </span>
                ) : (
                  <span className="text-indigo-600 font-medium">
                    {plugin.price > 0 ? `$${plugin.price}` : 'Free'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Plugin Detail Modal */}
      <AnimatePresence>
        {selectedPlugin && (
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
                  <div className="flex items-center gap-4">
                    <div className="text-6xl">{selectedPlugin.icon}</div>
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">{selectedPlugin.name}</h2>
                      <p className="text-gray-500">by {selectedPlugin.author} • v{selectedPlugin.version}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setSelectedPlugin(null)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <p className="text-gray-700 mb-6">{selectedPlugin.description}</p>

                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <Star className="w-5 h-5 text-amber-400 fill-amber-400 mx-auto mb-1" />
                    <div className="font-semibold text-gray-900">{selectedPlugin.rating}</div>
                    <div className="text-xs text-gray-500">{selectedPlugin.review_count} reviews</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <Download className="w-5 h-5 text-indigo-600 mx-auto mb-1" />
                    <div className="font-semibold text-gray-900">{selectedPlugin.download_count.toLocaleString()}</div>
                    <div className="text-xs text-gray-500">downloads</div>
                  </div>
                  <div className="bg-gray-50 rounded-xl p-4 text-center">
                    <Shield className="w-5 h-5 text-green-600 mx-auto mb-1" />
                    <div className="font-semibold text-gray-900">Verified</div>
                    <div className="text-xs text-gray-500">by Nexus</div>
                  </div>
                </div>

                <div className="mb-6">
                  <h3 className="font-semibold text-gray-900 mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-2">
                    {selectedPlugin.tags.map((tag) => (
                      <span key={tag} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="flex gap-3">
                  {installedPlugins.includes(selectedPlugin.id) ? (
                    <>
                      <button
                        onClick={() => {
                          uninstallPlugin(selectedPlugin);
                          setSelectedPlugin(null);
                        }}
                        className="flex-1 py-3 bg-red-100 text-red-700 rounded-xl font-medium hover:bg-red-200 transition-colors"
                      >
                        Uninstall
                      </button>
                      <button className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-medium hover:bg-indigo-700 transition-colors">
                        Configure
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => {
                        installPlugin(selectedPlugin);
                        setSelectedPlugin(null);
                      }}
                      disabled={isInstalling}
                      className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl font-medium hover:from-indigo-700 hover:to-violet-700 transition-all disabled:opacity-50"
                    >
                      {isInstalling ? 'Installing...' : selectedPlugin.price > 0 ? `Buy $${selectedPlugin.price}` : 'Install Free'}
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
