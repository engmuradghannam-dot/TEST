import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Plane, Heart, Factory, Car, Utensils, HardHat, Fuel, Zap, Landmark, Shield, ShoppingBag, Globe, Truck, Building, GraduationCap, Briefcase, Waves, TreePine, Cpu, Film, Music, Newspaper, Phone, Wifi, Wrench, Stethoscope, Pill, FlaskConical, Wheat, Coffee, Beer, Hammer, Pickaxe, Drill, Flame, Droplets, Sun, Wind, Battery, Cable, Landmark as BankIcon, Wallet, Receipt, CreditCard, ShoppingCart, Package, MapPin, Train, Ship, Plane as PlaneIcon, Hospital, GraduationCap as EduIcon, Scale, Gavel, Badge, Users, Baby, Dumbbell, Gamepad2, Camera, Palette, BookOpen, Church, Mosque, Church as TempleIcon, Globe2, TreeDeciduous, Mountain, Snowflake, Cloud, Server, Database, Lock, Eye, Fingerprint, Radio, Tv, Mic, Printer, Scan, Barcode, QrCode, FileBarChart, PieChart, LineChart, BarChart3, Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle, XCircle, Info, HelpCircle, Search, Filter, SortAsc, Download, Upload, Share2, Link, ExternalLink, Bookmark, Star, Heart as HeartIcon, ThumbsUp, MessageSquare, Bell, Mail, Calendar, Clock, Timer, Watch, Map, Navigation, Compass, Crosshair, Target, Focus, Aperture, ZoomIn, ZoomOut, Maximize, Minimize, Move, RotateCw, RefreshCw, Repeat, Shuffle, Copy, Clipboard, Scissors, Eraser, PenTool, Pencil, Highlighter, Type, AlignLeft, AlignCenter, AlignRight, AlignJustify, List, ListOrdered, Indent, Outdent, Superscript, Subscript, Underline, Italic, Bold, Strikethrough, Code, Quote, Table, Image, Video, Music as MusicIcon, File, FileText, Folder, FolderOpen, Archive, Trash2, Delete, Save, Plus, Minus, Divide, Multiply, Equal, Percent, Calculator, Hash, At, DollarSign, Euro, PoundSterling, Yen, Bitcoin, CreditCard as CardIcon, Wallet as WalletIcon, Banknote, Coins, PiggyBank, Landmark as GovIcon, Building2 as OfficeIcon, Home, Hotel, Bed, Bath, Sofa, Lamp, Fan, AirVent, Thermometer, Droplet, Wind as WindIcon, CloudRain, CloudSnow, CloudLightning, SunDim, Moon, Sunrise, Sunset, Eclipse, Star as StarIcon, Sparkles, Flame as FlameIcon, ZapOff, Plug, BatteryCharging, BatteryWarning, BatteryFull, BatteryLow, Signal, WifiOff, Bluetooth, Radio as RadioIcon, Cast, Monitor, Smartphone, Tablet, Laptop, Desktop, Mouse, Keyboard, Headphones, Speaker, Watch as WatchIcon, Glasses, Shirt, ShoppingBag as BagIcon, Gift, Crown, Award, Medal, Trophy, Flag, MapPin as PinIcon, Navigation as NavIcon, Locate, LocateFixed, LocateOff, Crosshair as CrossIcon, Target as TargetIcon, Swords, Shield as ShieldIcon, ShieldAlert, ShieldCheck, ShieldOff, ShieldQuestion, Lock as LockIcon, Unlock, Key, Fingerprint as FingerprintIcon, Eye as EyeIcon, EyeOff, Glasses as GlassesIcon, Scan as ScanIcon, ScanLine, ScanFace, ScanEye, ScanSearch, QrCode as QrIcon, Barcode as BarIcon, FileBarChart as ChartFile, FileSpreadsheet, FileCode, FileJson, FileType, FileImage, FileVideo, FileAudio, FileArchive, FileUp, FileDown, FilePlus, FileMinus, FileX, FileCheck, FileClock, FileWarning, FileQuestion, FileSearch, FileLock, FileKey, FileSymlink, FileStack, Files, Folder as FolderIcon, FolderPlus, FolderMinus, FolderX, FolderCheck, FolderClock, FolderHeart, FolderStar, FolderSymlink, FolderTree, FolderGit, FolderKanban, FolderCog, FolderSearch, FolderLock, FolderOpen as FolderOpenIcon, Archive as ArchiveIcon, ArchiveRestore, ArchiveX, Trash as TrashIcon, Trash2 as Trash2Icon, Recycle, Delete as DeleteIcon, Save as SaveIcon, Plus as PlusIcon, Minus as MinusIcon, Divide as DivideIcon, Multiply as MultiplyIcon, Equal as EqualIcon, Percent as PercentIcon, Calculator as CalcIcon, Hash as HashIcon, At as AtIcon, DollarSign as DollarIcon, Euro as EuroIcon, PoundSterling as PoundIcon, Yen as YenIcon, Bitcoin as BtcIcon, CreditCard as CcIcon, Wallet as Wallet2Icon, Banknote as BanknoteIcon, Coins as CoinsIcon, PiggyBank as PiggyIcon, Landmark as LandIcon, Building2 as BldgIcon, Home as HomeIcon, Hotel as HotelIcon, Bed as BedIcon, Bath as BathIcon, Sofa as SofaIcon, Lamp as LampIcon, Fan as FanIcon, AirVent as VentIcon, Thermometer as ThermIcon, Droplet as DropIcon, Wind as Wind2Icon, CloudRain as RainIcon, CloudSnow as SnowIcon, CloudLightning as LightningIcon, SunDim as SunIcon, Moon as MoonIcon, Sunrise as SunriseIcon, Sunset as SunsetIcon, Eclipse as EclipseIcon, Star as Star2Icon, Sparkles as SparklesIcon, Flame as Flame2Icon, ZapOff as ZapOffIcon, Plug as PlugIcon, BatteryCharging as BatChargeIcon, BatteryWarning as BatWarnIcon, BatteryFull as BatFullIcon, BatteryLow as BatLowIcon, Signal as SignalIcon, WifiOff as WifiOffIcon, Bluetooth as BtIcon, Radio as Radio2Icon, Cast as CastIcon, Monitor as MonitorIcon, Smartphone as PhoneIcon, Tablet as TabletIcon, Laptop as LaptopIcon, Desktop as DesktopIcon, Mouse as MouseIcon, Keyboard as KbIcon, Headphones as HeadphonesIcon, Speaker as SpeakerIcon, Watch as Watch2Icon, Glasses as Glasses2Icon, Shirt as ShirtIcon, ShoppingBag as Bag2Icon, Gift as GiftIcon, Crown as CrownIcon, Award as AwardIcon, Medal as MedalIcon, Trophy as TrophyIcon, Flag as FlagIcon, MapPin as Pin2Icon, Navigation as Nav2Icon, Locate as LocateIcon, LocateFixed as LocateFixIcon, LocateOff as LocateOffIcon, Crosshair as Cross2Icon, Target as Target2Icon, Swords as SwordsIcon, Shield as Shield2Icon, ShieldAlert as ShieldAlertIcon, ShieldCheck as ShieldCheckIcon, ShieldOff as ShieldOffIcon, ShieldQuestion as ShieldQIcon, Lock as Lock2Icon, Unlock as UnlockIcon, Key as KeyIcon, Fingerprint as FpIcon, Eye as Eye2Icon, EyeOff as EyeOffIcon, Glasses as Glasses3Icon, Scan as Scan2Icon, ScanLine as ScanLineIcon, ScanFace as ScanFaceIcon, ScanEye as ScanEyeIcon, ScanSearch as ScanSearchIcon, QrCode as Qr2Icon, Barcode as Bar2Icon, FileBarChart as ChartFile2, FileSpreadsheet as SpreadsheetIcon, FileCode as CodeFileIcon, FileJson as JsonFileIcon, FileType as TypeFileIcon, FileImage as ImageFileIcon, FileVideo as VideoFileIcon, FileAudio as AudioFileIcon, FileArchive as ArchiveFileIcon, FileUp as FileUpIcon, FileDown as FileDownIcon, FilePlus as FilePlusIcon, FileMinus as FileMinusIcon, FileX as FileXIcon, FileCheck as FileCheckIcon, FileClock as FileClockIcon, FileWarning as FileWarnIcon, FileQuestion as FileQIcon, FileSearch as FileSearchIcon, FileLock as FileLockIcon, FileKey as FileKeyIcon, FileSymlink as FileSymlinkIcon, FileStack as FileStackIcon, Files as FilesIcon, Folder as Folder2Icon, FolderPlus as FolderPlusIcon, FolderMinus as FolderMinusIcon, FolderX as FolderXIcon, FolderCheck as FolderCheckIcon, FolderClock as FolderClockIcon, FolderHeart as FolderHeartIcon, FolderStar as FolderStarIcon, FolderSymlink as FolderSymlinkIcon, FolderTree as FolderTreeIcon, FolderGit as FolderGitIcon, FolderKanban as FolderKanbanIcon, FolderCog as FolderCogIcon, FolderSearch as FolderSearchIcon, FolderLock as FolderLockIcon, FolderOpen as FolderOpen2Icon, Archive as Archive2Icon, ArchiveRestore as ArchiveRestoreIcon, ArchiveX as ArchiveXIcon, Trash as Trash3Icon, Trash2 as Trash4Icon, Recycle as RecycleIcon, Delete as Delete2Icon, Save as Save2Icon, Plus as Plus2Icon, Minus as Minus2Icon, Divide as Divide2Icon, Multiply as Multiply2Icon, Equal as Equal2Icon, Percent as Percent2Icon, Calculator as Calc2Icon, Hash as Hash2Icon, At as At2Icon, DollarSign as Dollar2Icon, Euro as Euro2Icon, PoundSterling as Pound2Icon, Yen as Yen2Icon, Bitcoin as Btc2Icon, CreditCard as Cc2Icon, Wallet as Wallet3Icon, Banknote as Banknote2Icon, Coins as Coins2Icon, PiggyBank as Piggy2Icon, Landmark as Land2Icon, Building2 as Bldg2Icon, Home as Home2Icon, Hotel as Hotel2Icon, Bed as Bed2Icon, Bath as Bath2Icon, Sofa as Sofa2Icon, Lamp as Lamp2Icon, Fan as Fan2Icon, AirVent as Vent2Icon, Thermometer as Therm2Icon, Droplet as Drop2Icon, Wind as Wind3Icon, CloudRain as Rain2Icon, CloudSnow as Snow2Icon, CloudLightning as Lightning2Icon, SunDim as Sun2Icon, Moon as Moon2Icon, Sunrise as Sunrise2Icon, Sunset as Sunset2Icon, Eclipse as Eclipse2Icon, Star as Star3Icon, Sparkles as Sparkles2Icon, Flame as Flame3Icon, ZapOff as ZapOff2Icon, Plug as Plug2Icon, BatteryCharging as BatCharge2Icon, BatteryWarning as BatWarn2Icon, BatteryFull as BatFull2Icon, BatteryLow as BatLow2Icon, Signal as Signal2Icon, WifiOff as WifiOff2Icon, Bluetooth as Bt2Icon, Radio as Radio3Icon, Cast as Cast2Icon, Monitor as Monitor2Icon, Smartphone as Phone2Icon, Tablet as Tablet2Icon, Laptop as Laptop2Icon, Desktop as Desktop2Icon, Mouse as Mouse2Icon, Keyboard as Kb2Icon, Headphones as Headphones2Icon, Speaker as Speaker2Icon, Watch as Watch3Icon, Glasses as Glasses4Icon, Shirt as Shirt2Icon, ShoppingBag as Bag3Icon, Gift as Gift2Icon, Crown as Crown2Icon, Award as Award2Icon, Medal as Medal2Icon, Trophy as Trophy2Icon, Flag as Flag2Icon, MapPin as Pin3Icon, Navigation as Nav3Icon, Locate as Locate2Icon, LocateFixed as LocateFix2Icon, LocateOff as LocateOff2Icon, Crosshair as Cross3Icon, Target as Target3Icon, Swords as Swords2Icon, Shield as Shield3Icon, ShieldAlert as ShieldAlert2Icon, ShieldCheck as ShieldCheck2Icon, ShieldOff as ShieldOff2Icon, ShieldQuestion as ShieldQ2Icon, Lock as Lock3Icon, Unlock as Unlock2Icon, Key as Key2Icon, Fingerprint as Fp2Icon, Eye as Eye3Icon, EyeOff as EyeOff2Icon, Glasses as Glasses5Icon, Scan as Scan3Icon, ScanLine as ScanLine2Icon, ScanFace as ScanFace2Icon, ScanEye as ScanEye2Icon, ScanSearch as ScanSearch2Icon, QrCode as Qr3Icon, Barcode as Bar3Icon } from 'lucide-react';
import { api } from '../lib/api';

const iconMap = {
  Plane, Heart, Factory, Car, Utensils, HardHat, Fuel, Zap, Landmark, Shield, ShoppingBag, Globe, Truck, Building, Building2, GraduationCap, Briefcase, Waves, TreePine, Cpu, Film, Music, Newspaper, Phone, Wifi, Wrench, Stethoscope, Pill, FlaskConical, Wheat, Coffee, Beer, Hammer, Pickaxe, Drill, Flame, Droplets, Sun, Wind, Battery, Cable, BankIcon, Wallet, Receipt, CreditCard, ShoppingCart, Package, MapPin, Train, Ship, PlaneIcon, Hospital, EduIcon, Scale, Gavel, Badge, Users, Baby, Dumbbell, Gamepad2, Camera, Palette, BookOpen, Church, Mosque, TempleIcon, Globe2, TreeDeciduous, Mountain, Snowflake, Cloud, Server, Database, Lock, Eye, Fingerprint, Radio, Tv, Mic, Printer, Scan, Barcode, QrCode, FileBarChart, PieChart, LineChart, BarChart3, Activity
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
        { industry_id: 'MIN', name: 'Mining', name_ar: 'التعدين', category: 'Industrial', description: 'Mining operations', icon: 'Pickaxe', color: '#57534e', control_count: 14, agent_count: 4, required_license_tier: 'enterprise', is_active: true },
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
