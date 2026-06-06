import {
  Mountain,
  Wheat,
  TreePine,
  Droplets,
  Wind,
  Bug,
  Castle,
  Swords,
  Handshake,
  MessageSquare,
  AlertTriangle,
  Shield,
  Flame,
  ScrollText,
  Zap,
  Crown,
  Skull,
  Trophy,
  MapPin,
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Eye,
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Settings,
  Plus,
  Trash2,
  ChevronRight,
  ChevronLeft,
  X,
  Info,
  Timer,
  type LucideIcon,
} from 'lucide-react';

/* ============================================================
   Region Type Icons — 地形图标
   ============================================================ */
export const REGION_ICONS: Record<string, LucideIcon> = {
  mountain: Mountain,
  plain: Wheat,
  forest: TreePine,
  river: Droplets,
  desert: Wind,
  swamp: Bug,
  city: Castle,
};

export function getRegionIcon(type: string): LucideIcon {
  return REGION_ICONS[type] || MapPin;
}

/* ============================================================
   Event Type Icons — 事件图标
   ============================================================ */
export const EVENT_ICONS: Record<string, LucideIcon> = {
  battle: Swords,
  diplomacy: Handshake,
  natural_disaster: AlertTriangle,
  resource_discovery: Flame,
  sect_crisis: Shield,
  alliance_formed: Handshake,
  betrayal: Skull,
  breakthrough: Zap,
  trade: ScrollText,
  war_declaration: Swords,
  peace_treaty: Handshake,
  annexation: Crown,
  rebellion: Flame,
  treasure_found: Trophy,
  plague: Bug,
};

export function getEventIcon(type: string): LucideIcon {
  return EVENT_ICONS[type] || MessageSquare;
}

/* ============================================================
   Action Icons — 操作图标
   ============================================================ */
export const ACTION_ICONS: Record<string, LucideIcon> = {
  attack: Swords,
  defend: Shield,
  expand: TrendingUp,
  retreat: TrendingDown,
  trade: ScrollText,
  ally: Handshake,
  spy: Eye,
  breakthrough: Zap,
  gather: Flame,
};

export function getActionIcon(action: string): LucideIcon {
  return ACTION_ICONS[action] || Zap;
}

/* ============================================================
   Action Labels — 操作中文标签（无 emoji）
   ============================================================ */
export const ACTION_LABELS: Record<string, string> = {
  attack: '进攻',
  defend: '防御',
  expand: '扩张',
  retreat: '撤退',
  trade: '交易',
  ally: '结盟',
  spy: '谍报',
  breakthrough: '突破',
  gather: '采集',
  diplomacy: '外交',
  battle: '战斗',
  natural_disaster: '天灾',
  resource_discovery: '资源发现',
  sect_crisis: '宗门危机',
  alliance_formed: '联盟成立',
  betrayal: '背叛',
  war_declaration: '宣战',
  peace_treaty: '和平条约',
  annexation: '吞并',
  rebellion: '叛乱',
  treasure_found: '宝藏发现',
  plague: '瘟疫',
};

export function getActionLabel(action: string): string {
  return ACTION_LABELS[action] || action;
}

/* ============================================================
   UI Icons — 界面通用图标导出
   ============================================================ */
export {
  Mountain,
  Wheat,
  TreePine,
  Droplets,
  Wind,
  Bug,
  Castle,
  Swords,
  Handshake,
  MessageSquare,
  AlertTriangle,
  Shield,
  Flame,
  ScrollText,
  Zap,
  Crown,
  Skull,
  Trophy,
  MapPin,
  Users,
  TrendingUp,
  TrendingDown,
  Minus,
  Eye,
  Play,
  Pause,
  SkipForward,
  RotateCcw,
  Settings,
  Plus,
  Trash2,
  ChevronRight,
  ChevronLeft,
  X,
  Info,
  Timer,
};