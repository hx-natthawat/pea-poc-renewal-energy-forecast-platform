# F004: Mobile-Responsive Dashboard (PWA)

## Feature Overview

| Attribute | Value |
|-----------|-------|
| Feature ID | F004 |
| Version | v1.1.0 |
| Status | 📋 Planned |
| Priority | P2 - Nice to Have |

## Description

Full Progressive Web App (PWA) support for mobile devices with responsive layouts, touch-friendly interactions, offline data caching, and push notifications. Enables field operators to monitor the system on mobile devices.

**Reference**: v1.1.0 Roadmap - Mobile-Responsive Dashboard

## Requirements

### Functional Requirements

| ID | Requirement | Status |
|----|-------------|--------|
| F004-R01 | Responsive layout for all components | 📋 Planned |
| F004-R02 | Touch-friendly chart interactions | 📋 Planned |
| F004-R03 | Mobile navigation menu (hamburger) | 📋 Planned |
| F004-R04 | PWA manifest configuration | 📋 Planned |
| F004-R05 | Service worker for offline support | 📋 Planned |
| F004-R06 | Offline data caching | 📋 Planned |
| F004-R07 | Push notifications | 📋 Planned |
| F004-R08 | Install prompt (Add to Home Screen) | 📋 Planned |

### Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| F004-NF01 | Mobile load time | < 3 seconds (3G) |
| F004-NF02 | Lighthouse PWA score | ≥ 90 |
| F004-NF03 | Offline functionality | Core dashboards |
| F004-NF04 | Touch target size | ≥ 44px |

## Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column, stacked |
| Tablet | 640px - 1024px | Two column grid |
| Desktop | > 1024px | Full multi-column |

## PWA Configuration

### manifest.json

```json
{
  "name": "PEA RE Forecast Platform",
  "short_name": "PEA Forecast",
  "description": "Renewable Energy Forecasting Dashboard",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#2563eb",
  "orientation": "any",
  "icons": [
    {
      "src": "/icons/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icons/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker Strategy

```javascript
// Cache strategies
const CACHE_STRATEGIES = {
  // Network first for API calls
  api: 'NetworkFirst',

  // Cache first for static assets
  static: 'CacheFirst',

  // Stale while revalidate for dashboard data
  dashboard: 'StaleWhileRevalidate'
};

// Offline fallback
const OFFLINE_PAGES = [
  '/dashboard',
  '/solar',
  '/voltage',
  '/alerts'
];
```

## Mobile Components

### Touch-Friendly Charts

```tsx
// Mobile-optimized chart configuration
const mobileChartConfig = {
  tooltip: {
    trigger: 'axis',
    triggerOn: 'click',  // Tap instead of hover
  },
  dataZoom: {
    type: 'inside',
    zoomOnMouseWheel: false,
    moveOnMouseMove: false,
    preventDefaultMouseMove: true,
  },
  // Larger touch targets
  symbolSize: 12,
};
```

### Mobile Navigation

```tsx
// Hamburger menu for mobile
<Sheet>
  <SheetTrigger asChild>
    <Button variant="ghost" size="icon" className="md:hidden">
      <Menu className="h-6 w-6" />
    </Button>
  </SheetTrigger>
  <SheetContent side="left">
    <nav className="flex flex-col space-y-4">
      <Link href="/dashboard">Dashboard</Link>
      <Link href="/solar">Solar Forecast</Link>
      <Link href="/voltage">Voltage</Link>
      <Link href="/alerts">Alerts</Link>
    </nav>
  </SheetContent>
</Sheet>
```

## Implementation Plan

| Component | File | Priority |
|-----------|------|----------|
| PWA Manifest | `frontend/public/manifest.json` | P1 |
| Service Worker | `frontend/public/sw.js` | P1 |
| Mobile Layout | `frontend/src/components/layout/MobileLayout.tsx` | P1 |
| Mobile Navigation | `frontend/src/components/layout/MobileNav.tsx` | P1 |
| Responsive Charts | `frontend/src/components/charts/ResponsiveChart.tsx` | P2 |
| Push Notifications | `frontend/src/lib/push-notifications.ts` | P2 |
| Offline Storage | `frontend/src/lib/offline-storage.ts` | P2 |

## Testing Checklist

### Device Testing

- [ ] iPhone SE (375px)
- [ ] iPhone 12/13/14 (390px)
- [ ] iPad Mini (768px)
- [ ] iPad Pro (1024px)
- [ ] Android phones (various)

### PWA Testing

- [ ] Install prompt appears
- [ ] App installs correctly
- [ ] Offline mode works
- [ ] Push notifications received
- [ ] Background sync functional

## Acceptance Criteria

- [ ] Responsive layout on all breakpoints
- [ ] Touch interactions work smoothly
- [ ] PWA installable (Lighthouse check)
- [ ] Offline dashboard accessible
- [ ] Push notifications functional
- [ ] Service worker caching assets
- [ ] Lighthouse PWA score ≥ 90
- [ ] No horizontal scroll on mobile
- [ ] Touch targets ≥ 44px

---

*Feature Version: 1.0*
*Created: December 2025*
