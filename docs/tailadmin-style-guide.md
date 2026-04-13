# TailAdmin Style Guide

This document contains a comprehensive analysis of the TailAdmin free Tailwind dashboard template's visual design system. It extracts all CSS styles, utility classes, and styling configurations with pixel-perfect precision based on Tailwind CSS v4 and the template's custom implementation.

## 1. Typography

The template uses the **Outfit** font family across the entire application.

```css
--font-outfit: Outfit, sans-serif;
```

### Headings (Title)
| Level | Font Size | Line Height |
|-------|-----------|-------------|
| 2XL   | 72px      | 90px        |
| XL    | 60px      | 72px        |
| LG    | 48px      | 60px        |
| MD    | 36px      | 44px        |
| SM    | 30px      | 38px        |

### Theme Text (Body & Utilities)
| Level | Font Size | Line Height |
|-------|-----------|-------------|
| XL    | 20px      | 30px        |
| SM    | 14px      | 20px        |
| XS    | 12px      | 18px        |

---

## 2. Color Palette

TailAdmin extends the default Tailwind palette with custom semantic colors and neutral grays.

### Brand (Primary)
- `--color-brand-25`: #f2f7ff
- `--color-brand-50`: #ecf3ff
- `--color-brand-100`: #dde9ff
- `--color-brand-200`: #c2d6ff
- `--color-brand-300`: #9cb9ff
- `--color-brand-400`: #7592ff
- `--color-brand-500`: #465fff *(Base)*
- `--color-brand-600`: #3641f5
- `--color-brand-700`: #2a31d8
- `--color-brand-800`: #252dae
- `--color-brand-900`: #262e89
- `--color-brand-950`: #161950

### Neutral (Gray)
- `--color-gray-25`: #fcfcfd
- `--color-gray-50`: #f9fafb *(Background)*
- `--color-gray-100`: #f2f4f7
- `--color-gray-200`: #e4e7ec *(Borders)*
- `--color-gray-300`: #d0d5dd
- `--color-gray-400`: #98a2b3
- `--color-gray-500`: #667085
- `--color-gray-600`: #475467
- `--color-gray-700`: #344054
- `--color-gray-800`: #1d2939
- `--color-gray-900`: #101828
- `--color-gray-950`: #0c111d
- `--color-gray-dark`: #1a2231

### Semantic Colors
**Success (Green)**
Base: `--color-success-500`: #12b76a

**Error (Red)**
Base: `--color-error-500`: #f04438

**Warning (Yellow/Orange)**
Base: `--color-warning-500`: #f79009

**Orange**
Base: `--color-orange-500`: #fb6514

**Light Blue**
Base: `--color-blue-light-500`: #0ba5ec

**Additional Theme Colors**
- Pink: `--color-theme-pink-500`: #ee46bc
- Purple: `--color-theme-purple-500`: #7a5af8

---

## 3. Shadows & Z-Index

### Shadows
- **XS**: `0px 1px 2px 0px rgba(16, 24, 40, 0.05)`
- **SM**: `0px 1px 3px 0px rgba(16, 24, 40, 0.1), 0px 1px 2px 0px rgba(16, 24, 40, 0.06)`
- **MD**: `0px 4px 8px -2px rgba(16, 24, 40, 0.1), 0px 2px 4px -2px rgba(16, 24, 40, 0.06)`
- **LG**: `0px 12px 16px -4px rgba(16, 24, 40, 0.08), 0px 4px 6px -2px rgba(16, 24, 40, 0.03)`
- **XL**: `0px 20px 24px -4px rgba(16, 24, 40, 0.08), 0px 8px 8px -4px rgba(16, 24, 40, 0.03)`
- **4XL (Drop Shadow)**: `0 35px 35px rgba(0, 0, 0, 0.25), 0 45px 65px rgba(0, 0, 0, 0.15)`

### Component Specific Shadows
- **Focus Ring**: `0px 0px 0px 4px rgba(70, 95, 255, 0.12)`
- **Tooltip**: `0px 4px 6px -2px rgba(16, 24, 40, 0.05), -8px 0px 20px 8px rgba(16, 24, 40, 0.05)`
- **Datepicker**: `-5px 0 0 #262d3c, 5px 0 0 #262d3c`
- **Slider Navigation**: `0px 1px 2px 0px rgba(16, 24, 40, 0.1), 0px 1px 3px 0px rgba(16, 24, 40, 0.1)`

### Z-Index
Available variables: `1, 9, 99, 999, 9999, 99999, 999999`

---

## 4. Responsive Breakpoints

TailAdmin adds two extra small breakpoints and one large breakpoint to default Tailwind:
- `2xsm`: 375px
- `xsm`: 425px
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px
- `3xl`: 2000px

---

## 5. Custom Utilities & Components

### Menu / Sidebar Items
TailAdmin implements custom `@utility` directives for the sidebar navigation.

- **`.menu-item`**: Base styling for sidebar links (`text-theme-sm relative flex items-center gap-3 rounded-lg px-3 py-2 font-medium`)
- **`.menu-item-active`**: Active state (`bg-brand-50 text-brand-500 dark:bg-brand-500/[0.12] dark:text-brand-400`)
- **`.menu-item-inactive`**: Inactive hover state
- **`.menu-item-icon-*`**: Icon fill color management
- **`.menu-item-arrow-*`**: Dropdown arrow styling and rotation

### Scrollbars
- **`.no-scrollbar`**: Hides scrollbar completely but allows scrolling
- **`.custom-scrollbar`**: 
  - Width: `size-1.5`
  - Track: `rounded-full`
  - Thumb: `rounded-full bg-gray-200` (Dark mode: `#344054`)

### Form Elements
- **Checkbox (Table)**: 
  ```css
  .tableCheckbox:checked ~ span span { @apply opacity-100; }
  .tableCheckbox:checked ~ span { @apply border-brand-500 bg-brand-500; }
  ```
- **Task List Checkbox**: Strikethrough effect on check.

### 3rd Party Integrations

#### ApexCharts
- Overrides tooltips to match theme shadows and border radius.
- Enforces font family and colors on labels.
- `plotOptions` config used in charts: `columnWidth: "39%", borderRadius: 5`

#### Flatpickr (Date Picker)
- Calendar styled with `.flatpickr-calendar` to match shadows and border radii.
- Selected days use brand color `#465fff`.
- In-range selection uses custom box-shadows to fill gaps between days.

#### FullCalendar
- Styled `.fc-button-group` to match template buttons.
- Event colors matched to semantic palette (`fc-bg-success`, `fc-bg-danger`, etc.).

#### Swiper (Carousel)
- Navigation buttons styled with glassmorphism (`bg-white/90 backdrop-blur-[10px]`).
- Pagination bullets transition from small circles to wide pills on active state (`w-6.5 rounded-xl`).

---

## 6. Components

### Buttons
TailAdmin provides several button variants with specific padding, border radius, and transition effects.

**Primary Button**
```html
<button class="inline-flex items-center gap-2 rounded-lg bg-brand-500 px-5 py-3.5 text-sm font-medium text-white shadow-theme-xs transition hover:bg-brand-600">
  Button Text
</button>
```
- Smaller padding variant: `px-4 py-3`

**Secondary Button (Outline)**
```html
<button class="inline-flex items-center gap-2 rounded-lg bg-white px-5 py-3.5 text-sm font-medium text-gray-700 shadow-theme-xs ring-1 ring-inset ring-gray-300 transition hover:bg-gray-50 dark:bg-gray-800 dark:text-gray-400 dark:ring-gray-700 dark:hover:bg-white/[0.03]">
  Button Text
</button>
```

### Forms
Form inputs feature consistent heights, border radii, and distinct focus states.

**Default Text Input**
```html
<input type="text" class="h-11 w-full rounded-lg border border-gray-300 bg-transparent px-4 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:bg-dark-900 dark:text-white/90 dark:placeholder:text-white/30 dark:focus:border-brand-800" />
```
- Height: `h-11`
- Focus Ring: `focus:ring-3 focus:ring-brand-500/10`
- Border Color on Focus: `focus:border-brand-300`

**Select Input**
```html
<select class="appearance-none h-11 w-full rounded-lg border border-gray-300 bg-transparent bg-none px-4 py-2.5 pr-11 text-sm text-gray-800 shadow-theme-xs focus:border-brand-300 focus:outline-hidden focus:ring-3 focus:ring-brand-500/10 dark:border-gray-700 dark:bg-gray-900 dark:bg-dark-900 dark:text-white/90 dark:focus:border-brand-800">
  <option>Select Option</option>
</select>
```

### Tables
Tables are designed with clean borders, clear typography for headers, and integrated status pills.

**Table Container**
```html
<div class="overflow-hidden rounded-2xl border border-gray-200 bg-white px-4 pb-3 pt-4 sm:px-6 dark:border-gray-800 dark:bg-white/[0.03]">
  <div class="w-full overflow-x-auto">
    <table class="min-w-full">...</table>
  </div>
</div>
```

**Table Header**
```html
<tr class="border-y border-gray-100 dark:border-gray-800">
  <th class="py-3">
    <p class="text-theme-xs font-medium text-gray-500 dark:text-gray-400">Column Name</p>
  </th>
</tr>
```

**Status Pills (Inside Table)**
- **Success:** `rounded-full bg-success-50 px-2 py-0.5 text-theme-xs font-medium text-success-600 dark:bg-success-500/15 dark:text-success-500`
- **Warning:** `rounded-full bg-warning-50 px-2 py-0.5 text-theme-xs font-medium text-warning-600 dark:bg-warning-500/15 dark:text-warning-500`
- **Error:** `rounded-full bg-error-50 px-2 py-0.5 text-theme-xs font-medium text-error-600 dark:bg-error-500/15 dark:text-error-500`

### Cards
Dashboard cards use specific border, background, and shadow utilities to separate content from the main background.

```html
<div class="rounded-2xl border border-gray-200 bg-white p-5 sm:p-6 dark:border-gray-800 dark:bg-white/[0.03]">
  <!-- Card Content -->
</div>
```

### Charts
Charts leverage ApexCharts and define consistent plot options across the dashboard to match the rounded style.

**Bar Chart (Chart 01)**
- `columnWidth`: "39%"
- `borderRadius`: 5

**Radial Bar Chart (Chart 02 - Progress)**
- Type: `radialBar`
- Start Angle: `-90`
- End Angle: `90`
- Hollow Size: `80%`
- Track Background: `#E4E7EC`
- Track Margin: `5`
- Value Font Size: `36px`, Weight: `600`, Color: `#1D2939`
- Fill Color: `#465FFF` (Brand)

**Area Chart (Chart 03 - Sales & Revenue)**
- Type: `area`
- Colors: `#465FFF` (Brand) and `#9CB9FF` (Brand 300)
- Fill Gradient: `opacityFrom: 0.55`, `opacityTo: 0`
- Stroke: `curve: "straight"`, width `2`
- Grid: X-axis lines hidden, Y-axis lines shown

**Area/Line Chart Colors**
- Blue: `#465fff`
- Light Blue: `#0ba5ec`
- Green: `#12b76a`
- Orange: `#fb6514`

