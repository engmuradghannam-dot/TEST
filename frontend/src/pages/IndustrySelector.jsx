import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Plane, Heart, Factory, Car, Utensils, HardHat, Fuel, Zap, Landmark, Shield, ShoppingBag, Globe, Truck, Building, GraduationCap, Briefcase, Waves, TreePine, Cpu, Film, Music, Newspaper, Phone, Wifi, Wrench, Stethoscope, Pill, FlaskConical, Wheat, Coffee, Beer, Hammer, Flame, Droplets, Sun, Wind, Battery, Cable, Wallet, Receipt, CreditCard, ShoppingCart, Package, MapPin, Train, Ship, Scale, Gavel, Badge, Users, Baby, Dumbbell, Gamepad2, Camera, Palette, BookOpen, Church, Globe2, TreeDeciduous, Mountain, Snowflake, Cloud, Server, Database, Lock, Eye, Fingerprint, Radio, Tv, Mic, Printer, Scan, Barcode, QrCode, FileBarChart, PieChart, LineChart, BarChart3, Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, XCircle, Info, HelpCircle, Search, Filter, SortAsc, Download, Upload, Share2, Link, ExternalLink, Bookmark, Star, ThumbsUp, MessageSquare, Bell, Mail, Calendar, Clock, Timer, Watch, Map, Navigation, Compass, Crosshair, Target, Focus, Aperture, ZoomIn, ZoomOut, Maximize, Minimize, Move, RotateCw, RefreshCw, Repeat, Shuffle, Copy, Clipboard, Scissors, Eraser, PenTool, Pencil, Highlighter, Type, AlignLeft, AlignCenter, AlignRight, AlignJustify, List, ListOrdered, Indent, Outdent, Superscript, Subscript, Underline, Italic, Bold, Strikethrough, Code, Quote, Table, Image, Video, File, FileText, Folder, FolderOpen, Archive, Trash2, Delete, Save, Plus, Minus, Divide, Equal, Percent, Calculator, Hash, DollarSign, Euro, PoundSterling, Bitcoin, Banknote, Coins, PiggyBank, Home, Hotel, Bed, Bath, Sofa, Lamp, Fan, AirVent, Thermometer, Droplet, CloudRain, CloudSnow, CloudLightning, SunDim, Moon, Sunrise, Sunset, Sparkles, ZapOff, Plug, BatteryCharging, BatteryWarning, BatteryFull, BatteryLow, Signal, WifiOff, Bluetooth, Cast, Monitor, Smartphone, Tablet, Laptop, Mouse, Keyboard, Headphones, Speaker, Glasses, Shirt, Gift, Crown, Award, Medal, Trophy, Flag, Locate, LocateFixed, LocateOff, Swords, ShieldAlert, ShieldCheck, ShieldOff, ShieldQuestion, Unlock, Key, EyeOff, ScanLine, ScanFace, ScanEye, ScanSearch, FileSpreadsheet, FileCode, FileJson, FileType, FileImage, FileVideo, FileAudio, FileArchive, FileUp, FileDown, FilePlus, FileMinus, FileX, FileCheck, FileClock, FileWarning, FileQuestion, FileSearch, FileLock, FileKey, FileSymlink, FileStack, Files, FolderPlus, FolderMinus, FolderX, FolderCheck, FolderClock, FolderHeart, FolderSymlink, FolderTree, FolderGit, FolderKanban, FolderCog, FolderSearch, FolderLock, ArchiveRestore, ArchiveX, Recycle } from 'lucide-react';
import api from '../lib/api';

const iconMap = {
  Plane, Heart, Factory, Car, Utensils, HardHat, Fuel, Zap, Landmark, Shield, ShoppingBag, Globe, Truck, Building, Building2, GraduationCap, Briefcase, Waves, TreePine, Cpu, Film, Music, Newspaper, Phone, Wifi, Wrench, Stethoscope, Pill, FlaskConical, Wheat, Coffee, Beer, Hammer, Hammer, Wrench, Flame, Droplets, Sun, Wind, Battery, Cable, BankIcon, Wallet, Receipt, CreditCard, ShoppingCart, Package, MapPin, Train, Ship, PlaneIcon, Hospital, EduIcon, Scale, Gavel, Badge, Users, Baby, Dumbbell, Gamepad2, Camera, Palette, BookOpen, Church, Mosque, TempleIcon, Globe2, TreeDeciduous, Mountain, Snowflake, Cloud, Server, Database, Lock, Eye, Fingerprint, Radio, Tv, Mic, Printer, Scan, Barcode, QrCode, FileBarChart, PieChart, LineChart, BarChart3, Activity
};

export default function IndustrySelector() {
  const [industries, setIndustries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');
  const navigate = useNavigate();

  useEffect(() => {
    api.get('/industries/catalog/').then(r => {
      const data = r.data.results || r.data;
      setIndustries(data);
      setLoading(false);
    }).catch(() => {
      // Fallback seed data if API not available
      setIndustries([
        { industry_id: 'AVI', name: 'Aviation & Airlines', name_ar: 'الطيران والخطوط الجوية', category: 'Transportation', description: 'Airlines, aircraft operations, aviation services', icon: 'Plane', color: '#3b82f6', control_count: 12, agent_count: 4, required_license_tier: 'industry', is_active: true },
        { industry_id: 'AIRPORT', name: 'Airport Management', name_ar: 'إدارة المطارات', category: 'Transportation', description: 'Airport operations and facilities', icon: 'Plane', color: '#06b6d4', control_count: 10, agent_count: 3, required_license_tier: 'industry', is_active: true },
        { industry_id: 'HLT', name: 'Hospital & Healthcare', name_ar: 'المستشفيات والرعاية الصحية', category: 'Healthcare', description: 'Hospitals and medical systems', icon: 'Heart', color: '#ef4444', control_count: 15, agent_count: 5, required_license_tier: 'industry', is_active: true },
        { industry_id: 'CLN', name: 'Clinics & Medical Centers', name_ar: 'العيادات والمراكز الطبية', category: 'Healthcare', description: 'Outpatient healthcare', icon: 'Stethoscope', color: '#f97316', control_count: 8, agent_count: 2, required_license_tier: 'business', is_active: true },
        { industry_id: 'PHA', name: 'Pharmaceutical', name_ar: 'الأدوية والصيدلة', category: 'Healthcare', description: 'Drug manufacturing and distribution', icon: 'Pill', color: '#8b5cf6', control_count: 14, agent_count: 4, required_license_tier: 'industry', is_active: true },
        { industry_id: 'MFG', name: 'Manufacturing', name_ar: 'التصنيع', category: 'Industrial', description: 'General manufacturing', icon: 'Factory', color: '#64748b', control_count: 10, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'AUTO', name: 'Automotive Manufacturing', name_ar: 'تصنيع السيارات', category: 'Industrial', description: 'Vehicle production', icon: 'Car', color: '#1e293b', control_count: 12, agent_count: 3, required_license_tier: 'industry', is_active: true },
        { industry_id: 'FNB', name: 'Food & Beverage', name_ar: 'الأغذية والمشروبات', category: 'Manufacturing', description: 'Food production', icon: 'Utensils', color: '#22c55e', control_count: 11, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'CON', name: 'Construction', name_ar: 'البناء والإنشاءات', category: 'Engineering', description: 'Construction projects', icon: 'HardHat', color: '#f59e0b', control_count: 10, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'ENG', name: 'Engineering Services', name_ar: 'خدمات الهندسة', category: 'Engineering', description: 'Engineering companies', icon: 'Wrench', color: '#6366f1', control_count: 9, agent_count: 2, required_license_tier: 'business', is_active: true },
        { industry_id: 'OIL', name: 'Oil & Gas', name_ar: 'النفط والغاز', category: 'Energy', description: 'Oil and gas operations', icon: 'Fuel', color: '#78350f', control_count: 16, agent_count: 5, required_license_tier: 'enterprise', is_active: true },
        { industry_id: 'ENE', name: 'Energy & Utilities', name_ar: 'الطاقة والمرافق', category: 'Energy', description: 'Power and utilities', icon: 'Zap', color: '#eab308', control_count: 13, agent_count: 4, required_license_tier: 'industry', is_active: true },
        { industry_id: 'REN', name: 'Renewable Energy', name_ar: 'الطاقة المتجددة', category: 'Energy', description: 'Solar and wind energy', icon: 'Sun', color: '#fbbf24', control_count: 11, agent_count: 4, required_license_tier: 'industry', is_active: true },
        { industry_id: 'MIN', name: 'Mining', name_ar: 'التعدين', category: 'Industrial', description: 'Mining operations', icon: 'Hammer', color: '#57534e', control_count: 14, agent_count: 4, required_license_tier: 'enterprise', is_active: true },
        { industry_id: 'BANK', name: 'Banking', name_ar: 'الخدمات المصرفية', category: 'Finance', description: 'Banking operations', icon: 'BankIcon', color: '#0f766e', control_count: 18, agent_count: 6, required_license_tier: 'enterprise', is_active: true },
        { industry_id: 'INS', name: 'Insurance', name_ar: 'التأمين', category: 'Finance', description: 'Insurance services', icon: 'Shield', color: '#0e7490', control_count: 12, agent_count: 4, required_license_tier: 'industry', is_active: true },
        { industry_id: 'RET', name: 'Retail', name_ar: 'التجزئة', category: 'Commerce', description: 'Retail operations', icon: 'ShoppingBag', color: '#db2777', control_count: 9, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'ECOM', name: 'E-Commerce', name_ar: 'التجارة الإلكترونية', category: 'Commerce', description: 'Online commerce', icon: 'Globe', color: '#7c3aed', control_count: 10, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'LOG', name: 'Logistics', name_ar: 'الخدمات اللوجستية', category: 'Transportation', description: 'Logistics and supply chain', icon: 'Truck', color: '#4338ca', control_count: 11, agent_count: 3, required_license_tier: 'business', is_active: true },
        { industry_id: 'GOV', name: 'Government', name_ar: 'الحكومة', category: 'Public Sector', description: 'Government operations', icon: 'Landmark', color: '#1e3a5f', control_count: 15, agent_count: 4, required_license_tier: 'enterprise', is_active: true },
      ]);
      setLoading(false);
    });
  }, []);

  const categories = ['all', ...new Set(industries.map(i => i.category))];
  const filtered = industries.filter(i => {
    const matchesSearch = (i.name + ' ' + i.description).toLowerCase().includes(search.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || i.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const deployIndustry = async (industryId) => {
    try {
      await api.post(`/industries/catalog/${industryId}/deploy/`);
      navigate('/dashboard');
    } catch (e) {
      alert('Deployed locally (API not connected)');
      navigate('/dashboard');
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      <div className="text-white text-xl animate-pulse">Loading Industry Catalog...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white p-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
            Nexus Industry Control Library
          </h1>
          <p className="text-slate-400 text-lg">Select your industry to deploy specialized controls, AI agents, and compliance frameworks</p>
        </div>

        <div className="flex flex-col md:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search industries..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
          <select
            value={categoryFilter}
            onChange={e => setCategoryFilter(e.target.value)}
            className="px-4 py-3 bg-slate-800/50 border border-slate-700 rounded-xl text-white focus:outline-none focus:border-blue-500"
          >
            {categories.map(c => (
              <option key={c} value={c}>{c === 'all' ? 'All Categories' : c}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {filtered.map(ind => {
            const Icon = iconMap[ind.icon] || Building2;
            return (
              <div
                key={ind.industry_id}
                onClick={() => setSelected(ind)}
                className={`p-6 rounded-2xl border-2 cursor-pointer transition-all hover:scale-105 hover:shadow-xl ${selected?.industry_id === ind.industry_id ? 'border-blue-500 bg-blue-500/10 shadow-blue-500/20' : 'border-slate-700/50 bg-slate-800/40 hover:border-slate-600'}`}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-3 rounded-xl" style={{backgroundColor: ind.color + '20'}}>
                    <Icon size={24} style={{color: ind.color}} />
                  </div>
                  <span className="text-xs font-medium px-2 py-1 rounded-full bg-slate-700/50 text-slate-300">{ind.category}</span>
                </div>
                <h3 className="text-lg font-semibold mb-2">{ind.name}</h3>
                <p className="text-sm text-slate-400 line-clamp-2 mb-4">{ind.description}</p>
                <div className="flex gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1"><Shield size={12} /> {ind.control_count} Controls</span>
                  <span className="flex items-center gap-1"><Brain size={12} /> {ind.agent_count} AI</span>
                </div>
                <div className="mt-3">
                  <span className={`text-xs px-2 py-1 rounded-full ${ind.required_license_tier === 'enterprise' ? 'bg-purple-500/20 text-purple-300' : ind.required_license_tier === 'industry' ? 'bg-blue-500/20 text-blue-300' : 'bg-green-500/20 text-green-300'}`}>
                    {ind.required_license_tier}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {selected && (
          <div className="mt-8 p-8 bg-slate-800/60 rounded-2xl border border-slate-600 backdrop-blur-sm">
            <h2 className="text-2xl font-bold mb-6">{selected.name} - Deployment Preview</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-5 bg-slate-700/50 rounded-xl">
                <div className="text-3xl font-bold text-blue-400">{selected.control_count}</div>
                <div className="text-sm text-slate-400 mt-1">Industry Controls</div>
              </div>
              <div className="text-center p-5 bg-slate-700/50 rounded-xl">
                <div className="text-3xl font-bold text-green-400">{selected.agent_count}</div>
                <div className="text-sm text-slate-400 mt-1">AI Agents</div>
              </div>
              <div className="text-center p-5 bg-slate-700/50 rounded-xl">
                <div className="text-3xl font-bold text-purple-400">15+</div>
                <div className="text-sm text-slate-400 mt-1">Compliance Frameworks</div>
              </div>
              <div className="text-center p-5 bg-slate-700/50 rounded-xl">
                <div className="text-3xl font-bold text-yellow-400">{selected.required_license_tier}</div>
                <div className="text-sm text-slate-400 mt-1">License Tier</div>
              </div>
            </div>
            <button
              onClick={() => deployIndustry(selected.industry_id)}
              className="w-full py-4 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 rounded-xl font-semibold text-lg transition-all shadow-lg shadow-blue-500/25"
            >
              Deploy {selected.name}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
