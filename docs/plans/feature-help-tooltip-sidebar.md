# Feature Spec: Help Tooltip & Sidebar System

**Feature ID**: F-UI-001
**Status**: Complete
**Created**: December 7, 2025
**Completed**: December 7, 2025
**Priority**: P2 - UX Enhancement

---

## Overview

Implement a contextual help system that provides tool tips in each UI section. When clicked, these tooltips open a right sidebar displaying detailed information about the section, its features, and usage guidance.

## User Stories

1. **As a grid operator**, I want to see help icons next to dashboard sections so I can quickly understand what each visualization shows.
2. **As a new user**, I want to click a help icon and see detailed documentation in a sidebar so I can learn how to use the platform without leaving the page.
3. **As a power user**, I want to dismiss the help sidebar easily so it doesn't interfere with my workflow.

---

## Design Specification

### Visual Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  PEA RE Forecast Platform                              [?] [⚙] [👤]        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────────────────────────────────┐   ┌──────────────────┐  │
│  │  Solar Forecast                         [?]    │   │  HELP SIDEBAR    │  │
│  │  ─────────────────────────                     │   │  ─────────────── │  │
│  │                                                │   │                  │  │
│  │  ████████████████████████████████              │   │  📊 Solar        │  │
│  │  ████████████████████████████████              │   │     Forecast     │  │
│  │  ████████████████████████████████              │   │                  │  │
│  │                                                │   │  This chart      │  │
│  └────────────────────────────────────────────────┘   │  displays the    │  │
│                                                        │  predicted       │  │
│  ┌────────────────────────────────────────────────┐   │  solar power     │  │
│  │  Voltage Monitor                        [?]    │   │  output for      │  │
│  │  ─────────────────────                         │   │  your region.    │  │
│  │                                                │   │                  │  │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   │   │  Key Features:   │  │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   │   │  • Day-ahead     │  │
│  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓                   │   │  • Intraday      │  │
│  │                                                │   │  • Real-time     │  │
│  └────────────────────────────────────────────────┘   │                  │  │
│                                                        │  [📖 Full Docs]  │  │
│                                                        │                  │  │
│                                                        └──────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Interaction Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  User sees   │────▶│  User clicks │────▶│   Sidebar    │
│  [?] icon    │     │   [?] icon   │     │   opens      │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Sidebar    │◀────│  User clicks │◀────│  Shows help  │
│   closes     │     │   X or ESC   │     │  for section │
└──────────────┘     └──────────────┘     └──────────────┘
```

### Responsive Behavior

| Screen Size | Sidebar Behavior |
|-------------|------------------|
| Desktop (≥1024px) | Fixed right sidebar, pushes content |
| Tablet (640-1023px) | Overlay sidebar, 320px wide |
| Mobile (<640px) | Full-width bottom sheet, 60% height |

---

## Component Architecture

### File Structure

```
frontend/src/components/help/
├── index.ts                    # Barrel exports
├── HelpSidebar.tsx            # Main sidebar component
├── HelpTrigger.tsx            # [?] button component
├── HelpContent.tsx            # Content renderer
├── HelpSection.tsx            # Collapsible section
├── types.ts                   # TypeScript interfaces
└── content/
    ├── index.ts               # Content registry
    ├── overview.ts            # Overview tab help
    ├── solar.ts               # Solar forecast help
    ├── voltage.ts             # Voltage monitor help
    ├── grid.ts                # Grid operations help
    ├── alerts.ts              # Alert system help
    ├── history.ts             # Historical data help
    └── audit.ts               # Audit log help
```

### State Management (Zustand)

```typescript
// frontend/src/stores/helpStore.ts

interface HelpState {
  isOpen: boolean;
  activeSection: string | null;
  previousSection: string | null;

  // Actions
  openHelp: (sectionId: string) => void;
  closeHelp: () => void;
  toggleHelp: (sectionId: string) => void;
}
```

### Component Hierarchy

```
<DashboardShell>
  └── <HelpProvider>
        ├── <MainContent>
        │     ├── <SolarForecastChart>
        │     │     └── <HelpTrigger sectionId="solar-forecast" />
        │     ├── <VoltageMonitor>
        │     │     └── <HelpTrigger sectionId="voltage-monitor" />
        │     └── ...other components
        │
        └── <HelpSidebar />
```

---

## Component Specifications

### 1. HelpTrigger Component

**Purpose**: Clickable help icon that appears in section headers

```typescript
interface HelpTriggerProps {
  sectionId: string;           // Unique identifier for the section
  className?: string;          // Additional styling
  size?: 'sm' | 'md' | 'lg';  // Icon size (default: 'md')
  variant?: 'default' | 'subtle'; // Visual style
}
```

**Visual States**:
- Default: PEA purple icon with subtle hover effect
- Active: Filled icon when sidebar shows this section
- Disabled: Grey icon (for sections without help content)

**Accessibility**:
- `aria-label="Show help for {sectionName}"`
- `aria-expanded={isActive}`
- Keyboard focusable (Tab)
- Activates on Enter/Space

### 2. HelpSidebar Component

**Purpose**: Right-side panel displaying contextual help

```typescript
interface HelpSidebarProps {
  position?: 'right' | 'bottom';  // Responsive position
}
```

**Features**:
- Smooth slide-in animation (300ms)
- Close button (X icon)
- Section title with icon
- Scrollable content area
- "View Full Documentation" link
- Keyboard close (ESC key)
- Click-outside to close (mobile only)

**Layout**:
```
┌─────────────────────────┐
│ [←] Section Name    [X] │  <- Header
├─────────────────────────┤
│                         │
│  📊 Description         │  <- Content
│                         │
│  Key Features:          │
│  • Feature 1            │
│  • Feature 2            │
│                         │
│  ─────────────────────  │
│                         │
│  Related Topics:        │  <- Related
│  > Voltage Prediction   │
│  > Alert Management     │
│                         │
├─────────────────────────┤
│  [📖 Full Documentation]│  <- Footer
└─────────────────────────┘
```

### 3. HelpContent Interface

```typescript
interface HelpSection {
  id: string;
  title: string;
  titleTh: string;           // Thai translation
  icon: LucideIcon;
  description: string;
  descriptionTh: string;
  features: HelpFeature[];
  relatedSections?: string[];
  docsUrl?: string;
  tips?: string[];
}

interface HelpFeature {
  title: string;
  titleTh: string;
  description: string;
  descriptionTh: string;
}
```

---

## Help Content Definitions

### Dashboard Sections

| Section ID | Title | Icon | Description |
|------------|-------|------|-------------|
| `overview-summary` | Overview Summary | LayoutDashboard | Key metrics at a glance |
| `solar-forecast` | Solar Forecast | Sun | Predicted solar power output |
| `voltage-monitor` | Voltage Monitor | Zap | Real-time voltage levels |
| `network-topology` | Network Topology | Network | Prosumer distribution network |
| `alert-dashboard` | Alert Dashboard | Bell | Active alerts and notifications |
| `model-performance` | Model Performance | Activity | ML model accuracy metrics |
| `forecast-comparison` | Forecast Comparison | BarChart3 | Compare model predictions |
| `historical-analysis` | Historical Analysis | History | Past data exploration |
| `day-ahead-report` | Day-Ahead Report | Calendar | Tomorrow's forecast report |
| `load-forecast` | Load Forecast | TrendingUp | System load predictions |
| `demand-forecast` | Demand Forecast | BarChart2 | Energy demand forecasts |
| `imbalance-monitor` | Imbalance Monitor | Scale | Grid imbalance tracking |
| `audit-log` | Audit Log | Shield | System activity trail |

### Sample Content: Solar Forecast

```typescript
// content/solar.ts
export const solarForecastHelp: HelpSection = {
  id: 'solar-forecast',
  title: 'Solar Forecast',
  titleTh: 'พยากรณ์พลังงานแสงอาทิตย์',
  icon: Sun,
  description:
    'Displays predicted solar power output based on weather conditions, ' +
    'historical patterns, and ML model predictions. Accuracy target: MAPE < 10%.',
  descriptionTh:
    'แสดงกำลังผลิตไฟฟ้าพลังงานแสงอาทิตย์ที่คาดการณ์ไว้ ตามสภาพอากาศ ' +
    'รูปแบบในอดีต และการพยากรณ์ของโมเดล ML ความแม่นยำ: MAPE < 10%',
  features: [
    {
      title: 'Day-Ahead Forecast',
      titleTh: 'พยากรณ์ล่วงหน้า 1 วัน',
      description: 'See tomorrow\'s expected solar generation',
      descriptionTh: 'ดูการผลิตไฟฟ้าแสงอาทิตย์ที่คาดว่าจะเกิดขึ้นในวันพรุ่งนี้'
    },
    {
      title: 'Confidence Intervals',
      titleTh: 'ช่วงความเชื่อมั่น',
      description: 'Shaded areas show prediction uncertainty (80%, 95%)',
      descriptionTh: 'พื้นที่แรเงาแสดงความไม่แน่นอนของการพยากรณ์'
    },
    {
      title: 'Actual vs Predicted',
      titleTh: 'ค่าจริง vs ค่าพยากรณ์',
      description: 'Compare real-time actuals against forecasted values',
      descriptionTh: 'เปรียบเทียบค่าจริงแบบ real-time กับค่าที่พยากรณ์ไว้'
    }
  ],
  relatedSections: ['model-performance', 'forecast-comparison', 'day-ahead-report'],
  docsUrl: '/docs/solar-forecast',
  tips: [
    'Use the time range selector to zoom into specific periods',
    'Click on data points to see exact values',
    'Export data using the download button'
  ]
};
```

---

## Implementation Tasks

### Phase 1: Foundation (Priority: High)

| Task | Description | Estimate | Depends On |
|------|-------------|----------|------------|
| T1.1 | Create `stores/helpStore.ts` with Zustand | 30 min | - |
| T1.2 | Create `components/help/types.ts` interfaces | 30 min | - |
| T1.3 | Create `HelpTrigger.tsx` component | 1 hr | T1.1, T1.2 |
| T1.4 | Create `HelpSidebar.tsx` component | 2 hr | T1.1, T1.2 |

### Phase 2: Content (Priority: High)

| Task | Description | Estimate | Depends On |
|------|-------------|----------|------------|
| T2.1 | Create content registry structure | 30 min | T1.2 |
| T2.2 | Write Overview tab help content | 30 min | T2.1 |
| T2.3 | Write Solar forecast help content | 30 min | T2.1 |
| T2.4 | Write Voltage monitor help content | 30 min | T2.1 |
| T2.5 | Write Grid operations help content | 30 min | T2.1 |
| T2.6 | Write Alerts help content | 30 min | T2.1 |
| T2.7 | Write History help content | 30 min | T2.1 |
| T2.8 | Write Audit log help content | 30 min | T2.1 |

### Phase 3: Integration (Priority: Medium)

| Task | Description | Estimate | Depends On |
|------|-------------|----------|------------|
| T3.1 | Integrate with DashboardShell layout | 1 hr | T1.4 |
| T3.2 | Add HelpTrigger to Overview summary cards | 30 min | T1.3, T2.2 |
| T3.3 | Add HelpTrigger to Solar components | 30 min | T1.3, T2.3 |
| T3.4 | Add HelpTrigger to Voltage components | 30 min | T1.3, T2.4 |
| T3.5 | Add HelpTrigger to Grid components | 30 min | T1.3, T2.5 |
| T3.6 | Add HelpTrigger to Alert components | 30 min | T1.3, T2.6 |
| T3.7 | Add HelpTrigger to History components | 30 min | T1.3, T2.7 |
| T3.8 | Add HelpTrigger to Audit page | 30 min | T1.3, T2.8 |

### Phase 4: Polish (Priority: Low)

| Task | Description | Estimate | Depends On |
|------|-------------|----------|------------|
| T4.1 | Add keyboard navigation (ESC to close) | 30 min | T1.4 |
| T4.2 | Add slide animation with Tailwind | 30 min | T1.4 |
| T4.3 | Add mobile bottom sheet behavior | 1 hr | T1.4 |
| T4.4 | Add "View Full Docs" link | 30 min | T1.4 |
| T4.5 | Add related sections navigation | 30 min | T2.x |
| T4.6 | Add Thai language toggle | 1 hr | T2.x |

### Phase 5: Testing (Priority: Medium)

| Task | Description | Estimate | Depends On |
|------|-------------|----------|------------|
| T5.1 | Unit tests for HelpTrigger | 30 min | T1.3 |
| T5.2 | Unit tests for HelpSidebar | 30 min | T1.4 |
| T5.3 | Integration test for sidebar flow | 1 hr | T3.x |
| T5.4 | Accessibility audit (ARIA, keyboard) | 1 hr | T4.x |

---

## Acceptance Criteria

### Functional Requirements

- [ ] Each dashboard section has a visible [?] help trigger icon
- [ ] Clicking the help trigger opens the right sidebar
- [ ] Sidebar displays relevant help content for the clicked section
- [ ] Sidebar can be closed via X button, ESC key, or clicking outside (mobile)
- [ ] Sidebar shows Thai and English content
- [ ] Related sections are clickable to navigate between help topics
- [ ] "View Full Documentation" links to external docs

### Non-Functional Requirements

- [ ] Sidebar animation is smooth (60fps)
- [ ] Works on desktop, tablet, and mobile
- [ ] Meets WCAG 2.1 AA accessibility standards
- [ ] Help content loads lazily (code-split)
- [ ] No layout shift when sidebar opens on desktop

### Performance Targets

- [ ] Sidebar opens in < 100ms
- [ ] Bundle size increase < 20KB
- [ ] No impact on initial page load

---

## Technical Notes

### Dependencies (Already Available)

- `lucide-react` - Icons (HelpCircle, X, ChevronRight)
- `zustand` - State management
- `clsx` + `tailwind-merge` - Styling utilities
- `framer-motion` - Animation (optional, not currently installed)

### Animation Approach

Use Tailwind CSS transitions (no additional dependencies):

```tsx
// HelpSidebar animation classes
const sidebarClasses = cn(
  'fixed right-0 top-0 h-full bg-white shadow-xl',
  'transition-transform duration-300 ease-in-out',
  isOpen ? 'translate-x-0' : 'translate-x-full'
);
```

### Mobile Bottom Sheet

For mobile, use CSS transforms with touch gesture support:

```tsx
// Mobile sheet behavior
const mobileClasses = cn(
  'fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-xl',
  'transition-transform duration-300',
  isOpen ? 'translate-y-0' : 'translate-y-full'
);
```

---

## Related Documents

- [CLAUDE.md](../../CLAUDE.md) - Project conventions
- [RELEASE-STATUS.md](../RELEASE-STATUS.md) - Current release status
- [Frontend Architecture](../architecture/frontend.md) - Component patterns

---

*Document Version: 1.0.0*
*Last Updated: December 7, 2025*
