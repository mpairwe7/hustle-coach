# 3. Frontend Setup — HustleCoach

## Routes (6 pages)

| Path | Page | Description |
|------|------|-------------|
| `/` | Landing | Hero + features + CTA |
| `/auth` | Auth | Login/signup |
| `/chat` | Chat | Main coaching interface |
| `/dashboard` | Dashboard | Stats, milestones, business doctor |
| `/leaderboard` | Leaderboard | National rankings |
| `/settings` | Settings | Profile, language, theme |

## Components (20+)

### Navigation
- NavSidebar — 3-level nav (top bar + sidebar + bottom nav)
- BottomNav — mobile tab bar (Home, Coach, Dashboard, Leaders, Settings)
- DomainNav — business domain pill selector

### Chat
- ChatInput — message input + voice
- ChatMessage — response with markdown, citations, domain badges
- StarterPrompts — domain-specific prompts
- BusinessPlanCard — structured business plan display

### Dashboard
- StatsOverview — KPI cards
- HealthRing — business health ring chart
- MilestoneList — milestone tracker
- ProfileEditor — profile editor
- BusinessDoctor — health diagnostic widget

### Voice & Utilities
- VoiceModal — voice chat UI
- OfflineIndicator — connectivity status
- Markdown — markdown renderer
- Skeleton — loading states

## State Management

- **useChatStore**: conversations, messages, streaming
- **useDashboardStore**: stats, milestones, profile
- **useAuthStore**: user, token, auth flow
