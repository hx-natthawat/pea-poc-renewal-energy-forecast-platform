# PEA RE Forecast Platform - Design Guidelines

> Based on **PEA Brand Bible 2022** and Official Mascot Color Guide

---

## Table of Contents

1. [Brand Colors](#brand-colors)
2. [Mascot Color Palette](#mascot-color-palette)
3. [Extended Color System](#extended-color-system)
4. [Typography](#typography)
5. [Component Styles](#component-styles)
6. [Dashboard Layout](#dashboard-layout)
7. [Tailwind CSS Configuration](#tailwind-css-configuration)
8. [Accessibility](#accessibility)
9. [Icons & Spacing](#icons--spacing)

---

## Brand Colors

### Primary Colors (สีประจำองค์กร)

| Color          | Hex       | RGB                | CMYK           | Pantone | Usage                        |
| -------------- | --------- | ------------------ | -------------- | ------- | ---------------------------- |
| **PEA Purple** | `#74045F` | rgb(116, 4, 95)    | C34 M98 Y0 K41 | 7650 C  | Primary brand, headers, CTAs |
| **PEA Gold**   | `#C7911B` | rgb(199, 145, 27)  | C6 M35 Y99 K18 | 1245 C  | Accents, highlights, success |
| **White**      | `#FFFFFF` | rgb(255, 255, 255) | C0 M0 Y0 K0    | -       | Backgrounds, text on dark    |

### Color Meanings (ค่าสีหลัก)

| Color             | Thai                     | Meaning                       |
| ----------------- | ------------------------ | ----------------------------- |
| **Purple (สีม่วง)** | พลังอำนาจ ความสง่า ศักดิ์ศรี    | Power, dignity, prestige      |
| **Gold (สีทอง)**   | ความเจริญรุ่งเรือง           | Prosperity, success           |
| **White (สีขาว)**  | ความดี ความสว่าง ความบริสุทธิ์ | Purity, brightness, innocence |

---

## Mascot Color Palette

The PEA mascot uses a specific set of colors as defined in the official Color Guide.

![Mascot Reference](design/mascot.png)

### Gold/Lightning Colors (สีทอง/สายฟ้า)

| Swatch           | Hex       | RGB           | CMYK             | Pantone | Usage                    |
| ---------------- | --------- | ------------- | ---------------- | ------- | ------------------------ |
| **Gold Primary** | `#C7911B` | R199 G145 B27 | C6 M35 Y99 K18   | 1245    | Lightning bolts, accents |
| **Gold Dark**    | `#966428` | R150 G100 B40 | C40 M65 Y100 K10 | -       | Gold shadows, depth      |
| **Gold Bright**  | `#FAC83C` | R250 G200 B60 | C1 M20 Y90 K0    | -       | Highlights, glows        |

### Purple/Body Colors (สีม่วง/ลำตัว)

| Swatch             | Hex       | RGB           | CMYK             | Pantone | Usage             |
| ------------------ | --------- | ------------- | ---------------- | ------- | ----------------- |
| **Purple Primary** | `#74045F` | R116 G4 B95   | C34 M98 Y0 K41   | 7650    | Main body color   |
| **Purple Dark**    | `#51124D` | R81 G18 B77   | C65 M100 Y30 K40 | -       | Shadows, outlines |
| **Magenta**        | `#C73E8A` | R199 G62 B138 | C20 M90 Y10 K0   | -       | Bright highlights |

### Accent Colors (สีเสริม)

| Swatch    | Hex       | RGB            | CMYK           | Pantone  | Usage                    |
| --------- | --------- | -------------- | -------------- | -------- | ------------------------ |
| **Pink**  | `#C86E8C` | R200 G110 B140 | C0 M60 Y10 K20 | P 74-4 C | Soft accents, highlights |
| **Black** | `#000000` | R0 G0 B0       | C0 M0 Y0 K100  | -        | Outlines, text           |
| **White** | `#FFFFFF` | R255 G255 B255 | C0 M0 Y0 K0    | -        | Face, highlights         |

---

## Extended Color System

### CSS Custom Properties

```css
:root {
  /* === PRIMARY BRAND COLORS === */
  --pea-purple: #74045F;
  --pea-purple-light: #8B1A75;
  --pea-purple-dark: #51124D;
  --pea-purple-muted: #5A0349;

  /* === SECONDARY BRAND COLORS === */
  --pea-gold: #C7911B;
  --pea-gold-light: #D4A43D;
  --pea-gold-dark: #966428;
  --pea-gold-bright: #FAC83C;

  /* === MASCOT ACCENT COLORS === */
  --pea-magenta: #C73E8A;
  --pea-pink: #C86E8C;

  /* === NEUTRAL PALETTE === */
  --pea-white: #FFFFFF;
  --pea-black: #000000;
  --pea-gray-50: #F9FAFB;
  --pea-gray-100: #F3F4F6;
  --pea-gray-200: #E5E7EB;
  --pea-gray-300: #D1D5DB;
  --pea-gray-400: #9CA3AF;
  --pea-gray-500: #6B7280;
  --pea-gray-600: #4B5563;
  --pea-gray-700: #374151;
  --pea-gray-800: #1F2937;
  --pea-gray-900: #111827;

  /* === SEMANTIC COLORS === */
  --pea-success: #10B981;
  --pea-success-light: #D1FAE5;
  --pea-warning: #F59E0B;
  --pea-warning-light: #FEF3C7;
  --pea-error: #EF4444;
  --pea-error-light: #FEE2E2;
  --pea-info: #3B82F6;
  --pea-info-light: #DBEAFE;
}
```

### Color Usage Guidelines

| Context                 | Primary         | Secondary                    | Background            |
| ----------------------- | --------------- | ---------------------------- | --------------------- |
| **Headers**             | `--pea-purple`  | `--pea-gold`                 | White/Gray-50         |
| **Buttons (Primary)**   | `--pea-purple`  | White text                   | -                     |
| **Buttons (Secondary)** | `--pea-gold`    | White text                   | -                     |
| **Links**               | `--pea-purple`  | `--pea-purple-dark` on hover | -                     |
| **Success States**      | `--pea-success` | `--pea-gold`                 | `--pea-success-light` |
| **Warning States**      | `--pea-warning` | `--pea-gold-dark`            | `--pea-warning-light` |
| **Error States**        | `--pea-error`   | -                            | `--pea-error-light`   |
| **Charts (Solar)**      | `--pea-gold`    | `--pea-purple`               | -                     |
| **Charts (Voltage)**    | `--pea-purple`  | `--pea-gold`                 | -                     |

---

## Typography

### Primary Font: Prompt

For Thai language content, use **Prompt** font family as specified in the PEA Brand Bible.

```css
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

/* Font Stack */
font-family: 'Prompt', 'Noto Sans Thai', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Font Weights

| Weight    | Value | Usage                              |
| --------- | ----- | ---------------------------------- |
| Light     | 300   | Secondary text, captions, metadata |
| Regular   | 400   | Body text, paragraphs              |
| Medium    | 500   | Emphasis, subheadings, labels      |
| Semi-Bold | 600   | Section headings, card titles      |
| Bold      | 700   | Primary headings, CTAs, hero text  |

### Type Scale

```css
/* Headings */
.h1 { font-size: 2.25rem; line-height: 2.5rem; font-weight: 700; }   /* 36px */
.h2 { font-size: 1.875rem; line-height: 2.25rem; font-weight: 600; } /* 30px */
.h3 { font-size: 1.5rem; line-height: 2rem; font-weight: 600; }      /* 24px */
.h4 { font-size: 1.25rem; line-height: 1.75rem; font-weight: 500; }  /* 20px */
.h5 { font-size: 1.125rem; line-height: 1.75rem; font-weight: 500; } /* 18px */
.h6 { font-size: 1rem; line-height: 1.5rem; font-weight: 500; }      /* 16px */

/* Body Text */
.body-lg { font-size: 1.125rem; line-height: 1.75rem; font-weight: 400; } /* 18px */
.body { font-size: 1rem; line-height: 1.5rem; font-weight: 400; }         /* 16px */
.body-sm { font-size: 0.875rem; line-height: 1.25rem; font-weight: 400; } /* 14px */

/* Small Text */
.caption { font-size: 0.75rem; line-height: 1rem; font-weight: 300; }  /* 12px */
.overline { font-size: 0.625rem; line-height: 1rem; font-weight: 500; text-transform: uppercase; letter-spacing: 0.1em; } /* 10px */
```

---

## Component Styles

### Buttons

```css
/* Primary Button - Purple */
.btn-primary {
  background-color: var(--pea-purple);
  color: white;
  font-weight: 600;
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background-color: var(--pea-purple-dark);
  box-shadow: 0 4px 6px -1px rgba(116, 4, 95, 0.3);
}

/* Secondary Button - Gold */
.btn-secondary {
  background-color: var(--pea-gold);
  color: white;
  font-weight: 600;
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
}

.btn-secondary:hover {
  background-color: var(--pea-gold-dark);
}

/* Outline Button */
.btn-outline {
  border: 2px solid var(--pea-purple);
  color: var(--pea-purple);
  background: transparent;
  font-weight: 600;
  border-radius: 0.5rem;
  padding: 0.625rem 1.375rem;
}

.btn-outline:hover {
  background-color: var(--pea-purple);
  color: white;
}

/* Ghost Button */
.btn-ghost {
  color: var(--pea-purple);
  background: transparent;
  font-weight: 500;
}

.btn-ghost:hover {
  background-color: rgba(116, 4, 95, 0.1);
}
```

### Cards

```css
/* Base Card */
.card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1), 0 1px 2px rgba(0, 0, 0, 0.06);
  border-left: 4px solid var(--pea-purple);
}

/* Gold Accent Card */
.card-gold {
  border-left-color: var(--pea-gold);
}

/* Interactive Card */
.card-interactive {
  transition: all 0.2s ease;
  cursor: pointer;
}

.card-interactive:hover {
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transform: translateY(-2px);
}

/* Stat Card */
.card-stat {
  border-left: none;
  border-top: 4px solid var(--pea-gold);
}
```

### Header & Navigation

```css
/* Main Header */
.header {
  background: linear-gradient(135deg, var(--pea-purple) 0%, var(--pea-purple-dark) 100%);
  color: white;
}

/* Navigation Item */
.nav-item {
  color: rgba(255, 255, 255, 0.8);
  font-weight: 500;
  transition: color 0.2s ease;
}

.nav-item:hover,
.nav-item.active {
  color: white;
}

/* Active Indicator */
.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--pea-gold);
  border-radius: 3px 3px 0 0;
}
```

### Form Elements

```css
/* Input Field */
.input {
  border: 1px solid var(--pea-gray-300);
  border-radius: 0.5rem;
  padding: 0.625rem 0.875rem;
  font-size: 1rem;
  transition: all 0.2s ease;
}

.input:focus {
  outline: none;
  border-color: var(--pea-purple);
  box-shadow: 0 0 0 3px rgba(116, 4, 95, 0.1);
}

/* Select */
.select {
  border: 1px solid var(--pea-gray-300);
  border-radius: 0.5rem;
  padding: 0.625rem 2.5rem 0.625rem 0.875rem;
  background-image: url("data:image/svg+xml,...");
  background-position: right 0.75rem center;
  background-repeat: no-repeat;
}

/* Checkbox/Radio */
.checkbox:checked,
.radio:checked {
  background-color: var(--pea-purple);
  border-color: var(--pea-purple);
}
```

---

## Dashboard Layout

### Color Usage by Section

| Section               | Primary Color | Accent               | Background      |
| --------------------- | ------------- | -------------------- | --------------- |
| **Header/Navigation** | PEA Purple    | Gold highlights      | Purple gradient |
| **Sidebar**           | Gray-800      | Purple active states | Gray-900        |
| **Solar Forecast**    | Gold          | Purple charts        | White           |
| **Voltage Monitor**   | Purple        | Gold highlights      | White           |
| **Alerts (Critical)** | Error Red     | -                    | Error Light     |
| **Alerts (Warning)**  | Warning Amber | -                    | Warning Light   |
| **System Status**     | Success Green | Gray                 | Gray-50         |

### Chart Color Palettes

```javascript
// Solar/Energy Charts - Gold Theme
export const solarColors = {
  primary: '#C7911B',      // PEA Gold
  secondary: '#74045F',    // PEA Purple
  tertiary: '#10B981',     // Success green
  gradient: ['#C7911B', '#D4A43D', '#FAC83C'],
  area: 'rgba(199, 145, 27, 0.2)',
};

// Voltage Charts - Purple Theme
export const voltageColors = {
  primary: '#74045F',      // PEA Purple
  secondary: '#C7911B',    // PEA Gold
  phases: {
    A: '#74045F',          // Purple
    B: '#C7911B',          // Gold
    C: '#6B7280',          // Gray
  },
  limits: {
    upper: '#EF4444',      // Red
    lower: '#F59E0B',      // Amber
    nominal: '#10B981',    // Green
  },
};

// Status Colors
export const statusColors = {
  normal: '#10B981',       // Green
  warning: '#F59E0B',      // Amber
  critical: '#EF4444',     // Red
  offline: '#6B7280',      // Gray
};

// Categorical Colors (for multiple series)
export const categoricalColors = [
  '#74045F',  // Purple
  '#C7911B',  // Gold
  '#10B981',  // Green
  '#3B82F6',  // Blue
  '#F59E0B',  // Amber
  '#EC4899',  // Pink
  '#8B5CF6',  // Violet
  '#06B6D4',  // Cyan
];
```

---

## Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        pea: {
          // Primary
          purple: {
            DEFAULT: '#74045F',
            light: '#8B1A75',
            dark: '#51124D',
            muted: '#5A0349',
          },
          // Secondary
          gold: {
            DEFAULT: '#C7911B',
            light: '#D4A43D',
            dark: '#966428',
            bright: '#FAC83C',
          },
          // Mascot Accents
          magenta: '#C73E8A',
          pink: '#C86E8C',
        },
      },
      fontFamily: {
        prompt: ['Prompt', 'Noto Sans Thai', 'sans-serif'],
      },
      boxShadow: {
        'pea': '0 4px 6px -1px rgba(116, 4, 95, 0.1), 0 2px 4px -1px rgba(116, 4, 95, 0.06)',
        'pea-lg': '0 10px 15px -3px rgba(116, 4, 95, 0.1), 0 4px 6px -2px rgba(116, 4, 95, 0.05)',
      },
      backgroundImage: {
        'pea-gradient': 'linear-gradient(135deg, #74045F 0%, #51124D 100%)',
        'pea-gold-gradient': 'linear-gradient(135deg, #C7911B 0%, #966428 100%)',
      },
    },
  },
  plugins: [],
};
```

### Utility Classes Reference

```html
<!-- Background Colors -->
<div class="bg-pea-purple">Purple background</div>
<div class="bg-pea-gold">Gold background</div>
<div class="bg-pea-gradient">Gradient background</div>

<!-- Text Colors -->
<p class="text-pea-purple">Purple text</p>
<p class="text-pea-gold">Gold text</p>

<!-- Border Colors -->
<div class="border-l-4 border-pea-purple">Purple left border</div>
<div class="border-pea-gold">Gold border</div>

<!-- Hover States -->
<button class="bg-pea-purple hover:bg-pea-purple-dark">Button</button>
<a class="text-pea-purple hover:text-pea-purple-dark">Link</a>
```

---

## Accessibility

### Contrast Ratios

| Combination                      | Ratio  | WCAG Level           |
| -------------------------------- | ------ | -------------------- |
| PEA Purple (#74045F) on White    | 10.5:1 | AAA                  |
| White on PEA Purple              | 10.5:1 | AAA                  |
| PEA Gold (#C7911B) on White      | 3.2:1  | AA (Large text only) |
| PEA Gold Dark (#966428) on White | 5.1:1  | AA                   |
| White on PEA Gold                | 3.2:1  | AA (Large text only) |

### Accessibility Guidelines

1. **Use PEA Purple for body text** - Meets AAA contrast on white backgrounds
2. **Use Gold for accents only** - Not suitable for small body text on white
3. **Use Gold Dark for gold text** - When gold text is required, use the darker variant
4. **Provide focus indicators** - 3px outline in purple at 0.1 opacity
5. **Maintain minimum touch targets** - 44px x 44px for interactive elements

```css
/* Focus states for accessibility */
.focus-visible {
  outline: 3px solid rgba(116, 4, 95, 0.5);
  outline-offset: 2px;
}

/* Skip link for keyboard navigation */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--pea-purple);
  color: white;
  padding: 8px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

---

## Icons & Spacing

### Icon Library

Use **Lucide React** icons with consistent sizing:

| Context        | Size | Tailwind Class |
| -------------- | ---- | -------------- |
| Inline text    | 16px | `w-4 h-4`      |
| Navigation     | 20px | `w-5 h-5`      |
| Card headers   | 24px | `w-6 h-6`      |
| Feature icons  | 32px | `w-8 h-8`      |
| Hero icons     | 40px | `w-10 h-10`    |
| Large displays | 48px | `w-12 h-12`    |

### Icon Colors

```jsx
// Standard icon (inherits text color)
<Sun className="w-5 h-5" />

// Brand colored icons
<Zap className="w-5 h-5 text-pea-gold" />
<Activity className="w-5 h-5 text-pea-purple" />

// Status icons
<CheckCircle className="w-5 h-5 text-green-500" />
<AlertTriangle className="w-5 h-5 text-amber-500" />
<XCircle className="w-5 h-5 text-red-500" />
```

### Spacing Scale

Based on 4px base unit:

| Token      | Value | Usage                         |
| ---------- | ----- | ----------------------------- |
| `space-0`  | 0px   | -                             |
| `space-1`  | 4px   | Tight spacing, icon gaps      |
| `space-2`  | 8px   | Compact padding, small gaps   |
| `space-3`  | 12px  | Default icon-text spacing     |
| `space-4`  | 16px  | Default padding, section gaps |
| `space-5`  | 20px  | Medium spacing                |
| `space-6`  | 24px  | Card padding, group spacing   |
| `space-8`  | 32px  | Section padding               |
| `space-10` | 40px  | Large gaps                    |
| `space-12` | 48px  | Major section breaks          |
| `space-16` | 64px  | Page sections                 |

### Layout Grid

```css
/* Container widths */
.container-sm { max-width: 640px; }
.container-md { max-width: 768px; }
.container-lg { max-width: 1024px; }
.container-xl { max-width: 1280px; }
.container-2xl { max-width: 1536px; }

/* Grid columns */
.grid-dashboard {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: 1.5rem;
}
```

---

## Quick Reference

### Brand Colors (Copy-Paste)

```text
PEA Purple:     #74045F | rgb(116, 4, 95)   | Pantone 7650
PEA Purple Dark:#51124D | rgb(81, 18, 77)
PEA Gold:       #C7911B | rgb(199, 145, 27) | Pantone 1245
PEA Gold Dark:  #966428 | rgb(150, 100, 40)
PEA Magenta:    #C73E8A | rgb(199, 62, 138)
PEA Pink:       #C86E8C | rgb(200, 110, 140) | Pantone P 74-4 C
```

### Font Stack

```css
font-family: 'Prompt', 'Noto Sans Thai', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

---

*Design Guidelines v2.0 - Based on PEA Brand Bible 2022 & Official Mascot Color Guide*
*Last Updated: December 2025*
