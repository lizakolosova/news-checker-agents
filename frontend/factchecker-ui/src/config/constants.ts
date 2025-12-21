import {
  CheckCircle,
  XCircle,
  Minus,
  HelpCircle,
  Search,
  FileText,
  Database,
  Award
} from 'lucide-react';

export const API_CONFIG = {
  BASE_URL: 'http://localhost:8000',
  ENDPOINTS: {
    FACT_CHECK: '/fact-check/article',
  },
  STEP_INTERVAL_MS: 2500,
};

export const RATING_CONFIG = {
  true: {
    icon: CheckCircle,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    border: 'border-emerald-300',
    label: 'TRUE',
    emoji: '✅',
  },
  mostly_true: {
    icon: CheckCircle,
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-300',
    label: 'MOSTLY TRUE',
    emoji: '✓',
  },
  half_true: {
    icon: Minus,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-300',
    label: 'HALF TRUE',
    emoji: '◐',
  },
  mostly_false: {
    icon: XCircle,
    color: 'text-orange-600',
    bg: 'bg-orange-50',
    border: 'border-orange-300',
    label: 'MOSTLY FALSE',
    emoji: '✗',
  },
  false: {
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-300',
    label: 'FALSE',
    emoji: '❌',
  },
  unverifiable: {
    icon: HelpCircle,
    color: 'text-slate-600',
    bg: 'bg-slate-50',
    border: 'border-slate-300',
    label: 'UNVERIFIABLE',
    emoji: '❓',
  },
};

export const STANCE_CONFIG = {
  supports: {
    icon: CheckCircle,
    color: 'text-emerald-600',
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
  },
  refutes: {
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
  unclear: {
    icon: HelpCircle,
    color: 'text-slate-600',
    bg: 'bg-slate-50',
    border: 'border-slate-200',
  },
};

export const TIER_CONFIG = {
  'Tier 1 (Highly Credible)': {
    color: 'bg-emerald-100 text-emerald-700 border-emerald-200',
    icon: '🏆',
  },
  'Tier 2 (Credible)': {
    color: 'bg-blue-100 text-blue-700 border-blue-200',
    icon: '✓',
  },
  'Tier 3 (Moderate)': {
    color: 'bg-amber-100 text-amber-700 border-amber-200',
    icon: '•',
  },
  Unknown: {
    color: 'bg-slate-100 text-slate-700 border-slate-200',
    icon: '?',
  },
};

export const PIPELINE_STEPS = [
  {
    icon: FileText,
    label: 'Extracting Claims',
    desc: 'Identifying verifiable statements...',
  },
  {
    icon: Search,
    label: 'Researching Evidence',
    desc: 'Searching credible sources...',
  },
  {
    icon: Database,
    label: 'Evaluating Quality',
    desc: 'Assessing source credibility...',
  },
  {
    icon: Award,
    label: 'Rendering Verdict',
    desc: 'Synthesizing final ratings...',
  },
];

export const EXAMPLE_ARTICLES = [
  {
    title: 'Belgium Economic Report',
    text: "Belgium's GDP grew by 1.5% in 2023 according to official statistics. The unemployment rate remained stable at 5.6%. Consumer spending increased significantly in Q4.",
  },
  {
    title: 'EU Inflation Update',
    text: 'According to Eurostat, the annual inflation rate was 2.9% in December 2023. The European Central Bank stated it would keep interest rates unchanged. Euro area inflation fell from 10.6% in October 2022.',
  },
];

export const INPUT_CONSTRAINTS = {
  MIN_CLAIMS: 1,
  MAX_CLAIMS: 10,
  DEFAULT_CLAIMS: 5,
};
