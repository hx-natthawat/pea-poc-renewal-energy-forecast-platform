# PEA RE Forecast Platform - Design Guidelines

> Based on **PEA Brand Bible 2022**

## Brand Colors

### Primary Colors (สีประจำองค์กร)

| Color | Hex | RGB | Pantone | Usage |
|-------|-----|-----|---------|-------|
| **PEA Purple** | `#74045F` | rgb(116, 4, 95) | 7650 C | Primary brand, headers, CTAs |
| **PEA Gold** | `#C7911B` | rgb(199, 145, 27) | 1245 C | Accents, highlights, success |
| **White** | `#FFFFFF` | rgb(255, 255, 255) | 000 C | Backgrounds, text on dark |

### Color Meanings (ค่าสีหลัก)

1. **Purple (สีม่วง)**: Power, dignity, prestige (พลังอำนาจ ความสง่า ศักดิ์ศรี)
2. **Gold (สีทอง)**: Prosperity (ความเจริญรุ่งเรือง)
3. **White (สีขาว)**: Purity, brightness, innocence (ความดี ความสว่าง ความบริสุทธิ์)

### Extended Palette

```css
:root {
  /* Primary */
  --pea-purple: #74045F;
  --pea-purple-light: #8B1A75;
  --pea-purple-dark: #5A0349;

  /* Secondary */
  --pea-gold: #C7911B;
  --pea-gold-light: #D4A43D;
  --pea-gold-dark: #A67814;

  /* Neutral */
  --pea-white: #FFFFFF;
  --pea-gray-50: #F9FAFB;
  --pea-gray-100: #F3F4F6;
  --pea-gray-200: #E5E7EB;
  --pea-gray-300: #D1D5DB;
  --pea-gray-500: #6B7280;
  --pea-gray-700: #374151;
  --pea-gray-900: #111827;

  /* Semantic */
  --pea-success: #10B981;
  --pea-warning: #F59E0B;
  --pea-error: #EF4444;
  --pea-info: #3B82F6;
}
```

## Typography

### Primary Font: Prompt

For Thai language content, use **Prompt** font family as specified in the PEA Brand Bible.

```css
/* Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

/* Font Stack */
font-family: 'Prompt', 'Noto Sans Thai', sans-serif;
```

### Font Weights

| Weight | CSS | Usage |
|--------|-----|-------|
| Light | 300 | Secondary text, captions |
| Regular | 400 | Body text |
| Medium | 500 | Emphasis, subheadings |
| Semi-Bold | 600 | Headings |
| Bold | 700 | Primary headings, CTAs |

### Type Scale

```css
/* Headings */
h1: 2.25rem (36px) / font-weight: 700
h2: 1.875rem (30px) / font-weight: 600
h3: 1.5rem (24px) / font-weight: 600
h4: 1.25rem (20px) / font-weight: 500

/* Body */
body: 1rem (16px) / font-weight: 400
small: 0.875rem (14px) / font-weight: 400
caption: 0.75rem (12px) / font-weight: 300
```

## Component Styles

### Buttons

```css
/* Primary Button */
.btn-primary {
  background-color: var(--pea-purple);
  color: white;
  font-weight: 600;
  border-radius: 0.5rem;
  padding: 0.75rem 1.5rem;
}

.btn-primary:hover {
  background-color: var(--pea-purple-dark);
}

/* Secondary Button */
.btn-secondary {
  background-color: var(--pea-gold);
  color: white;
}

/* Outline Button */
.btn-outline {
  border: 2px solid var(--pea-purple);
  color: var(--pea-purple);
  background: transparent;
}
```

### Cards

```css
.card {
  background: white;
  border-radius: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border-left: 4px solid var(--pea-purple);
}

.card-highlight {
  border-left-color: var(--pea-gold);
}
```

### Header

```css
.header {
  background: linear-gradient(135deg, var(--pea-purple) 0%, var(--pea-purple-dark) 100%);
  color: white;
}
```

## Dashboard Layout

### Color Usage by Section

| Section | Primary Color | Accent |
|---------|---------------|--------|
| Header/Navigation | PEA Purple | Gold accents |
| Solar Forecast | Gold | Purple charts |
| Voltage Monitor | Purple | Gold highlights |
| Alerts | Red/Amber | - |
| System Status | Green/Gray | - |

### Chart Colors

```javascript
// Solar charts - Gold theme
const solarColors = {
  primary: '#C7911B',    // PEA Gold
  secondary: '#74045F',  // PEA Purple
  gradient: ['#C7911B', '#D4A43D', '#E8C87A'],
};

// Voltage charts - Purple theme
const voltageColors = {
  primary: '#74045F',    // PEA Purple
  secondary: '#C7911B',  // PEA Gold
  phases: {
    A: '#74045F',        // Purple
    B: '#C7911B',        // Gold
    C: '#6B7280',        // Gray
  }
};
```

## Tailwind CSS Configuration

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        pea: {
          purple: {
            DEFAULT: '#74045F',
            light: '#8B1A75',
            dark: '#5A0349',
          },
          gold: {
            DEFAULT: '#C7911B',
            light: '#D4A43D',
            dark: '#A67814',
          },
        },
      },
      fontFamily: {
        prompt: ['Prompt', 'Noto Sans Thai', 'sans-serif'],
      },
    },
  },
};
```

## Accessibility

- Ensure contrast ratio of at least 4.5:1 for text
- PEA Purple on white: 10.5:1 (AAA)
- PEA Gold on white: 3.2:1 (use darker variant for text)
- White on PEA Purple: 10.5:1 (AAA)

## Icons

Use **Lucide React** icons with consistent sizing:
- Navigation icons: 20px (w-5 h-5)
- Card icons: 24px (w-6 h-6)
- Feature icons: 40px (w-10 h-10)

## Spacing

Follow 4px base unit:
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px

---

*Design Guidelines v1.0 - Based on PEA Brand Bible 2022*
