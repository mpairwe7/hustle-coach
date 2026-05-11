/**
 * HustleScale API Client — centralized, typed, with error handling.
 */

// In the browser, requests go through the Next.js rewrite proxy (same-origin, no CORS).
// On the server (SSR), call the backend directly.
const API_URL =
  typeof window !== "undefined"
    ? ""  // same-origin — proxied via next.config.mjs rewrites
    : (process.env.INTERNAL_API_URL || "http://127.0.0.1:8808");

// ─── Types ───

export interface Citation {
  source: string;
  section?: string;
  topic?: string;
  preview: string;
}

export interface BudgetItem {
  item: string;
  amount_ugx: number;
  notes?: string;
}

export interface RiskItem {
  risk: string;
  likelihood: string;
  impact: string;
  mitigation: string;
}

export interface BusinessPlan {
  business_name?: string;
  executive_summary?: string;
  startup_budget?: BudgetItem[];
  total_startup_cost?: number;
  monthly_costs?: BudgetItem[];
  total_monthly_cost?: number;
  revenue_projection?: {
    monthly_revenue: number;
    monthly_profit: number;
    assumptions: string;
  };
  break_even?: { months: number; explanation: string };
  pricing_strategy?: string;
  marketing_script?: string;
  risks?: RiskItem[];
  next_steps?: string[];
  confidence?: string;
}

export interface ToolCallRecord {
  round: number;
  tool: string;
  input: Record<string, unknown>;
  output_preview: string;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  faithfulness: number;
  domain: string;
  confidence: string;
  disclaimer: string;
  business_plan?: BusinessPlan;
  tool_calls: ToolCallRecord[];
  follow_ups: string[];
}

export interface StreamChunk {
  token?: string;
  tool_progress?: string;
  done?: boolean;
  citations?: Citation[];
  faithfulness?: number;
  domain?: string;
  confidence?: string;
  disclaimer?: string;
  business_plan?: BusinessPlan;
  tool_calls?: ToolCallRecord[];
  follow_ups?: string[];
}

export interface AuthResponse {
  token: string;
  user_id: string;
  credits: number;
  name?: string;
}

export interface BusinessProfile {
  business_name: string;
  business_type: string;
  location: string;
  startup_capital_ugx: number;
  monthly_revenue_ugx: number;
  monthly_profit_ugx: number;
  employees: number;
  stage: string;
}

export interface Milestone {
  id: string;
  title: string;
  description: string;
  category: string;
  completed: boolean;
  completed_at: number | null;
}

export interface DashboardData {
  profile: BusinessProfile;
  milestones: Milestone[];
  health_score: number;
  total_milestones: number;
  completed_milestones: number;
  recommendations: string[];
  next_actions: string[];
}

export interface DoctorDiagnosis {
  area: string;
  status: string;
  finding: string;
  recommendation: string;
  priority: string;
}

export interface DoctorResult {
  overall_health: string;
  health_score: number;
  diagnosis: DoctorDiagnosis[];
  quick_wins: string[];
  growth_opportunities: string[];
  disclaimer: string;
}

export interface LeaderboardEntry {
  rank: number;
  name: string;
  business_type: string;
  location: string;
  stage: string;
  milestones_completed: number;
  months_active: number;
  badge: string;
}

export interface LeaderboardData {
  entries: LeaderboardEntry[];
  total_entrepreneurs: number;
  total_businesses_launched: number;
  total_jobs_created: number;
  impact_note: string;
}

export interface ImpactStats {
  total_users: number;
  businesses_planned: number;
  businesses_launched: number;
  jobs_created: number;
}

export interface PriceEntry {
  item: string;
  category: string;
  price_ugx: number;
  unit: string;
  location: string;
  trend: string;
  names_lg?: string;
  names_sw?: string;
}

export interface FundingSource {
  id: string;
  name: string;
  provider: string;
  type: string;
  amount_range: string;
  eligibility: string;
  how_to_apply: string;
  interest_rate: string;
  requirements: string[];
  target_sectors: string[];
}

export interface Domain {
  id: string;
  name: string;
  description: string;
  icon: string;
}

// ─── Error class ───

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// ─── Core fetch wrapper ───

async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("hustle-scale-token")
      : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let message = `Request failed (${res.status})`;
    try {
      const body = await res.json();
      message = body.detail || body.message || message;
    } catch {}
    throw new ApiError(res.status, message);
  }

  return res.json();
}

// ─── Auth API ───

export const authApi = {
  login(email: string, password: string) {
    return apiFetch<AuthResponse>("/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },

  signup(email: string, password: string, name: string) {
    return apiFetch<AuthResponse>("/v1/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, name }),
    });
  },

  me() {
    return apiFetch<Record<string, unknown>>("/v1/auth/me");
  },
};

// ─── Chat API ───

export const chatApi = {
  send(query: string, locale: string, sessionId: string, domain?: string) {
    return apiFetch<ChatResponse>("/v1/chat", {
      method: "POST",
      body: JSON.stringify({
        query,
        locale,
        session_id: sessionId,
        domain,
      }),
    });
  },

  stream(
    query: string,
    locale: string,
    sessionId: string,
    signal?: AbortSignal,
  ) {
    const token =
      typeof window !== "undefined"
        ? localStorage.getItem("hustle-scale-token")
        : null;

    return fetch(`${API_URL}/v1/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({
        query,
        locale,
        session_id: sessionId,
      }),
      signal,
    });
  },
};

// ─── Dashboard API ───

export const dashboardApi = {
  get() {
    return apiFetch<DashboardData>("/v1/dashboard");
  },

  updateMilestone(milestoneId: string, completed: boolean) {
    return apiFetch<{ status: string; milestone_id: string }>(
      "/v1/dashboard/milestone",
      {
        method: "PUT",
        body: JSON.stringify({ milestone_id: milestoneId, completed }),
      },
    );
  },

  updateProfile(profile: BusinessProfile) {
    return apiFetch<{ status: string; profile: BusinessProfile }>(
      "/v1/dashboard/profile",
      {
        method: "PUT",
        body: JSON.stringify(profile),
      },
    );
  },
};

// ─── Business Doctor API ───

export const doctorApi = {
  checkup(params: {
    business_type: string;
    monthly_revenue_ugx: number;
    monthly_costs_ugx: number;
    months_operating: number;
    employees: number;
    location: string;
  }) {
    return apiFetch<DoctorResult>("/v1/business-doctor", {
      method: "POST",
      body: JSON.stringify(params),
    });
  },
};

// ─── Funding API ───

export const fundingApi = {
  match(params: {
    business_type: string;
    location: string;
    capital_needed_ugx: number;
    stage: string;
  }) {
    return apiFetch<{ matches: FundingSource[]; total_available: number }>(
      "/v1/funding/match",
      {
        method: "POST",
        body: JSON.stringify(params),
      },
    );
  },

  getAll() {
    return apiFetch<{ sources: FundingSource[] }>("/v1/funding/all");
  },
};

// ─── Market Prices API ───

export const marketApi = {
  search(params: { category?: string; item?: string }) {
    return apiFetch<{ prices: PriceEntry[]; last_updated: string }>(
      "/v1/market-prices",
      {
        method: "POST",
        body: JSON.stringify(params),
      },
    );
  },

  categories() {
    return apiFetch<{ categories: string[] }>("/v1/market-prices/categories");
  },
};

// ─── Leaderboard & Impact API ───

export const leaderboardApi = {
  get() {
    return apiFetch<LeaderboardData>("/v1/leaderboard");
  },

  impact() {
    return apiFetch<ImpactStats>("/v1/impact");
  },
};

// ─── Domains API ───

export const domainsApi = {
  list() {
    return apiFetch<{ domains: Domain[] }>("/v1/domains");
  },
};

// ─── Feedback API ───

export const feedbackApi = {
  submit(messageId: string, rating: number, comment?: string) {
    return apiFetch<{ status: string; message_id: string }>("/v1/feedback", {
      method: "POST",
      body: JSON.stringify({
        message_id: messageId,
        rating,
        comment: comment || "",
      }),
    });
  },
};
