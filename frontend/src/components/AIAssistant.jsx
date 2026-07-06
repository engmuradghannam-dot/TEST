import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Bot, Send, User, Sparkles, Loader2, X,
  ChevronRight, Lightbulb, FileText, BarChart3,
  Workflow, Zap, MessageSquare
} from 'lucide-react';
import axios from 'axios';
import toast from 'react-hot-toast';

export default function AIAssistant({ isOpen, onClose, currentPage = '' }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'مرحباً! أنا مساعدك الذكي في نظام Nexus ERP. كيف يمكنني مساعدتك اليوم؟\n\nHello! I am your AI assistant in the Nexus ERP system. How can I help you today?',
      timestamp: new Date().toISOString(),
      suggestions: [
        { label: 'كيف أُنشئ فاتورة؟', icon: FileText },
        { label: 'How to create a purchase order?', icon: FileText },
        { label: 'تحليل الأداء المالي', icon: BarChart3 },
        { label: 'Generate workflow', icon: Workflow },
      ]
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async (text = input) => {
    if (!text.trim() || isLoading) return;

    const userMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('/api/ceos/ai/conversations/quick_ask/', {
        message: text,
        current_page: currentPage
      });

      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString(),
        sources: response.data.sources,
        tokens_used: response.data.tokens_used,
        suggestions: extractSuggestions(response.data.response)
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      toast.error('Failed to get response');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  const extractSuggestions = (text) => {
    const suggestions = [];
    if (text.includes('create') || text.includes('إنشاء')) {
      suggestions.push({ label: 'Create new document', icon: FileText });
    }
    if (text.includes('approve') || text.includes('موافقة')) {
      suggestions.push({ label: 'Go to approvals', icon: CheckCircle });
    }
    if (text.includes('report') || text.includes('تقرير')) {
      suggestions.push({ label: 'View reports', icon: BarChart3 });
    }
    return suggestions;
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  if (!isOpen) return null;

  return (
    <motion.div
      initial={{ opacity: 0, x: 400 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 400 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed right-0 top-0 h-full w-[420px] bg-white shadow-2xl z-50 flex flex-col border-l border-gray-200"
    >
      {/* Header */}
      <div className="bg-gradient-to-r from-indigo-600 to-violet-600 px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
            <Bot className="w-6 h-6 text-white" />
          </div>
          <div>
            <h3 className="text-white font-semibold">Nexus AI Assistant</h3>
            <p className="text-indigo-100 text-xs">Powered by GPT-4.1</p>
          </div>
        </div>
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0
              ${msg.role === 'user'
                ? 'bg-indigo-100'
                : 'bg-gradient-to-br from-violet-500 to-indigo-600'
              }`}
            >
              {msg.role === 'user' ? (
                <User className="w-4 h-4 text-indigo-600" />
              ) : (
                <Sparkles className="w-4 h-4 text-white" />
              )}
            </div>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3
              ${msg.role === 'user'
                ? 'bg-indigo-600 text-white rounded-tr-sm'
                : 'bg-gray-100 text-gray-800 rounded-tl-sm'
              }`}
            >
              <div className="text-sm whitespace-pre-wrap leading-relaxed">
                {msg.content}
              </div>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-2 border-t border-gray-200/50">
                  <p className="text-xs text-gray-500 mb-1">Sources:</p>
                  {msg.sources.map((source, i) => (
                    <div key={i} className="text-xs text-gray-600 bg-white/50 rounded px-2 py-1 mb-1">
                      {source.title || source.text?.substring(0, 100)}...
                    </div>
                  ))}
                </div>
              )}

              {/* Suggestions */}
              {msg.suggestions && msg.suggestions.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-2">
                  {msg.suggestions.map((sugg, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(sugg.label)}
                      className="flex items-center gap-1 px-3 py-1.5 bg-white/80 hover:bg-white rounded-full text-xs text-gray-700 transition-colors border border-gray-200"
                    >
                      <sugg.icon className="w-3 h-3" />
                      {sugg.label}
                    </button>
                  ))}
                </div>
              )}

              <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-indigo-200' : 'text-gray-400'}`}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </div>
            </div>
          </motion.div>
        ))}

        {isLoading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-3"
          >
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-indigo-600 flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask me anything... / اسألني أي شيء..."
            rows={1}
            className="flex-1 px-4 py-2.5 border border-gray-300 rounded-xl text-sm focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none max-h-32"
          />
          <button
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim()}
            className="w-10 h-10 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl flex items-center justify-center hover:from-indigo-700 hover:to-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2 text-center">
          Press Enter to send • Shift+Enter for new line
        </p>
      </div>
    </motion.div>
  );
}

// Missing import
import { CheckCircle } from 'lucide-react';
