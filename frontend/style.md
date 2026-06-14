# ClassSense — Frontend Design System
> Single source of truth for every screen in the ClassSense web application.
> Any AI assistant or developer building a new screen must follow this file exactly.

---

## 1. Project Identity

**Product:** ClassSense — Real-time classroom engagement monitoring system  
**Audience:** University instructors and administrators  
**Tone:** Clinical precision with calm authority. Not corporate, not playful. Think a well-designed medical dashboard — trustworthy, focused, no noise.

---

## 2. Color Palette

```
--color-bg:           #000000   /* True black — page background */
--color-surface:      #1A1A1A   /* Card, input, sidebar background */
--color-surface-2:    #242424   /* Elevated surface, hover state bg */
--color-border:       rgba(255,255,255,0.08)   /* Subtle borders */
--color-border-focus: rgba(255,255,255,0.20)   /* Input focus ring */

--color-text-primary:   #FFFFFF               /* Headings, primary labels */
--color-text-secondary: rgba(255,255,255,0.60) /* Descriptions, subtitles */
--color-text-muted:     rgba(255,255,255,0.30) /* Placeholders, hints */
--color-text-disabled:  rgba(255,255,255,0.15) /* Disabled states */

--color-brand:        #FFFFFF   /* Primary CTA — white on black */
--color-brand-text:   #000000   /* Text on primary CTA */

/* Engagement State Colors */
--color-attentive:    #4ADE80   /* Green — attentive students */
--color-confused:     #FACC15   /* Yellow — confused students */
--color-distracted:   #F87171   /* Red/soft — distracted students */

/* Data / Chart Accent */
--color-accent-blue:  #60A5FA   /* Trend lines, sparklines */
--color-accent-dim:   rgba(96,165,250,0.15)  /* Chart fill under line */
```

**Rule:** Never use off-white cream backgrounds. Never use colored brand accents (orange, purple etc.). The entire app lives in black and dark gray. Color is reserved exclusively for engagement state indicators.

---

## 3. Typography

```
Font Family:  "Inter", ui-sans-serif, system-ui, sans-serif
Weights used: 300, 400, 500, 600, 700
```

### Type Scale

| Role | Size | Weight | Color | Usage |
|---|---|---|---|---|
| Display | 3xl (30px) | 500 | text-primary | Page headings (Login, Dashboard title) |
| Title | xl (20px) | 600 | text-primary | Section headings, card titles |
| Body | sm (14px) | 400 | text-secondary | Descriptions, subtitles |
| Label | sm (14px) | 500 | text-primary | Form labels, nav items |
| Caption | xs (12px) | 400 | text-muted | Helper text, timestamps, badges |
| Metric | 4xl–6xl | 700 | text-primary | Engagement percentage, big numbers |
| Code/ID | sm (14px) | 400 | text-muted | Anonymous IDs, session IDs (monospace) |

### Rules
- `tracking-tight` on all headings
- `leading-relaxed` on all body/description text
- `antialiased` on body globally
- Never center-align body paragraphs. Center only short labels and metric values.

---

## 4. Spacing & Layout

```
Page padding (desktop):  p-4
Page padding (mobile):   p-2
Border radius (cards):   rounded-3xl
Border radius (inputs):  rounded-xl
Border radius (buttons): rounded-xl
Border radius (badges):  rounded-full
Gap between form fields: gap-4
Gap between sections:    space-y-8 (desktop), space-y-10 (mobile)
Sidebar width:           w-64
Content max-width:       max-w-xl (forms), max-w-6xl (dashboard)
```

**Two-column split used on auth screens:**
- Left column (Hero): `w-[52%]` — hidden on mobile, `lg:flex`
- Right column (Form): `flex-1`

**Dashboard layout:**
- Fixed sidebar left, scrollable main content right
- Sidebar: `h-screen sticky top-0 flex flex-col`
- Main: `flex-1 overflow-y-auto`

---

## 5. Component Patterns

### 5.1 Inputs

```
bg-[#1A1A1A]
border-none
rounded-xl
h-11
px-4
text-white
placeholder:text-white/20
focus:ring-2 focus:ring-white/20
focus:outline-none
text-sm
```

- Labels: `text-sm font-medium text-white mb-1.5 block`
- Helper text below input: `text-xs text-white/30 mt-1`
- Error text below input: `text-xs text-red-400 mt-1`
- Icon inside input (right): `absolute right-3 top-1/2 -translate-y-1/2 text-white/30 cursor-pointer hover:text-white/60`

### 5.2 Primary Button (CTA)

```
w-full h-14
bg-white text-black
font-semibold
rounded-xl
hover:bg-white/90
active:scale-[0.98]
transition-all duration-150
text-sm
```

### 5.3 Secondary / Ghost Button

```
bg-black
border border-white/10
rounded-xl
hover:bg-white/5
text-white text-sm font-medium
px-4 h-11
transition-colors duration-150
```

### 5.4 Social Auth Buttons

```
bg-black border border-white/10 rounded-xl
h-11 px-4
flex items-center justify-center gap-2
text-sm font-medium text-white
hover:bg-white/5
transition-colors duration-150
```

### 5.5 Cards

```
bg-[#1A1A1A]
rounded-3xl
p-6
border border-white/5
```

Elevated card (hover or selected):
```
bg-[#242424]
border-white/10
```

### 5.6 Badges / Status Pills

```
rounded-full px-3 py-1 text-xs font-medium
```

| State | Background | Text |
|---|---|---|
| Attentive / Active | bg-green-500/15 | text-green-400 |
| Confused / Warning | bg-yellow-500/15 | text-yellow-400 |
| Distracted / Error | bg-red-500/15 | text-red-400 |
| Neutral / Info | bg-white/10 | text-white/60 |

### 5.7 Dividers

```
border-t border-white/10
```

Divider with label (e.g. "Or"):
```html
<div class="relative">
  <div class="absolute inset-0 flex items-center">
    <div class="w-full border-t border-white/10"></div>
  </div>
  <div class="relative flex justify-center">
    <span class="bg-black px-4 text-xs font-medium text-white/40 uppercase tracking-widest">Or</span>
  </div>
</div>
```

### 5.8 Sidebar Nav Item

```
Active:
  bg-white/10 text-white rounded-xl font-medium

Inactive:
  text-white/40 hover:text-white hover:bg-white/5 rounded-xl font-normal

Both:
  flex items-center gap-3 px-3 py-2.5 text-sm transition-colors duration-150
```

### 5.9 Metric / Stat Card (Dashboard)

```
bg-[#1A1A1A] rounded-3xl p-6
```

Structure:
```
[Label — text-xs text-white/40 uppercase tracking-widest]
[Big Number — text-5xl font-bold text-white mt-2]
[Sub-label — text-xs text-white/30 mt-1]
[Optional: colored indicator bar or sparkline at bottom]
```

### 5.10 Engagement Progress Bar

```
h-1.5 rounded-full bg-white/10    /* track */

Fill color based on state:
  >70%  → bg-green-400
  40-70% → bg-yellow-400
  <40%  → bg-red-400
```

### 5.11 Step Indicator (used in auth flow)

```
Active step:
  bg-white text-black border border-white rounded-xl
  Number circle: bg-black text-white

Inactive step:
  bg-[#1A1A1A] text-white border-none rounded-xl
  Number circle: bg-white/10 text-white/40

Both:
  flex items-center gap-3 px-4 py-3 text-sm font-medium
```

---

## 6. Animation Guidelines

Use `motion/react` (`framer-motion`). Keep animations purposeful — this is a data tool, not a marketing site.

### Page / Section Entry
```js
initial={{ opacity: 0, y: 10 }}
animate={{ opacity: 1, y: 0 }}
transition={{ duration: 0.5, ease: "easeOut" }}
```

### Staggered List Entry (e.g. sidebar items, step list)
```js
// Parent
variants={{
  show: { transition: { staggerChildren: 0.08, delayChildren: 0.1 } }
}}

// Each child
variants={{
  hidden: { opacity: 0, y: 8 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.4 } }
}}
```

### Number / Metric Count-up
- Use a simple count-up effect on dashboard metric numbers when session data loads
- Duration: 1.2s, ease: "easeOut"

### Engagement Percentage Update (live)
- Animate the number with a spring transition, not a jump
- Progress bars animate width with `transition-all duration-700`

### Rules
- No bouncy springs on a data dashboard
- Respect `prefers-reduced-motion` — wrap all animations with a check
- Do not animate on every re-render. Entry animations fire once on mount only.

---

## 7. Screen-by-Screen Reference

### 7.1 Login / Sign Up Screen
- Two-column layout: left = full-height hero video, right = form
- Left column background: absolute positioned `<video>` with `autoPlay muted loop playsInline object-cover` — NO overlay, NO gradient on top of video
- Right column: centered form, `max-w-xl`, dark background
- Form fields: First Name, Last Name (2-col grid), Email, Password (with eye toggle)
- Social auth row: Google + GitHub as ghost buttons in a 2-col grid
- Primary CTA: "Create Account" / "Log In" — full-width white button
- Footer link: small text, `text-white/40`, centered

### 7.2 Dashboard (Live Session)
- Sidebar left (fixed), main content right
- Top of main: session info bar (course name, timer, status badge)
- Metric cards row: Engagement %, Attentive count, Confused count, Distracted count
- Center: Large engagement percentage as hero number
- Below: Recharts `LineChart` — engagement trend over last 30 data points
  - Line color: `#60A5FA`
  - Grid lines: `stroke="rgba(255,255,255,0.05)"`
  - Tooltip: dark bg `#1A1A1A`, border `rgba(255,255,255,0.1)`
  - No axis labels clutter — minimal tick marks only
- Bottom: Emotion distribution bars (attentive / confused / distracted)
- End Session button: top-right, ghost button with red tint on hover (`hover:border-red-500/30 hover:text-red-400`)

### 7.3 Start Session Screen
- Centered card, `max-w-md`
- Course name dropdown or text input
- Time slot input
- "Start Monitoring" — primary CTA button
- Back link at top-left

### 7.4 Session History Screen
- Full-width table inside a card
- Table headers: `text-xs uppercase tracking-widest text-white/30`
- Table rows: `border-b border-white/5 hover:bg-white/3`
- Engagement column: colored badge (green / yellow / red based on value)
- Actions column: "View" and "Export" as small ghost buttons

### 7.5 Session Summary Screen
- Two-column grid: left = pie chart (Recharts `PieChart`), right = summary stats
- Pie chart colors: green for attentive, yellow for confused, red for distracted
- Stats: Average, Peak, Min engagement as metric cards
- Download buttons row: "Download PDF" and "Download CSV" as ghost buttons with icons

### 7.6 Course Analytics Screen
- Line chart spanning full width showing engagement across all sessions of a course
- X-axis: session dates
- Y-axis: engagement percentage (0–100)
- Same chart styling as dashboard trend chart

### 7.7 Sidebar
- ClassSense logo/wordmark at top (`text-xl font-semibold tracking-tight`)
- Nav items with Lucide icons:
  - Dashboard (LayoutDashboard)
  - Sessions (Video)
  - History (Clock)
  - Analytics (TrendingUp)
  - Settings (Settings)
- Active item highlighted with `bg-white/10`
- User info at bottom (avatar placeholder circle + name + role)
- Logout button at very bottom

---

## 8. Icon Usage

Use `lucide-react` exclusively. Size convention:

| Context | Size class |
|---|---|
| Sidebar nav | `size-4` |
| Input prefix/suffix | `size-4` |
| Button icon | `size-4` |
| Empty state | `size-8 text-white/20` |
| Dashboard metric icon | `size-5` |

Color: always inherit from parent text color. Never set icon colors independently unless it is an engagement state icon.

---

## 9. Data Visualization (Recharts)

All charts share these base styles:

```js
// Chart container background: transparent (sits on card bg #1A1A1A)

// CartesianGrid
<CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />

// XAxis / YAxis
<XAxis tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 11 }} axisLine={false} tickLine={false} />
<YAxis tick={{ fill: 'rgba(255,255,255,0.25)', fontSize: 11 }} axisLine={false} tickLine={false} />

// Tooltip
<Tooltip
  contentStyle={{ backgroundColor: '#1A1A1A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '12px' }}
  labelStyle={{ color: 'rgba(255,255,255,0.5)', fontSize: '11px' }}
  itemStyle={{ color: '#fff', fontSize: '13px' }}
/>

// Line (trend)
<Line type="monotone" dataKey="pct" stroke="#60A5FA" strokeWidth={2} dot={false} />

// Pie chart cell colors
attentive:  #4ADE80
confused:   #FACC15
distracted: #F87171
```

---

## 10. Responsive Breakpoints

```
Mobile (<640px):   Single column, stacked layout, no sidebar (hamburger)
Tablet (640–1024): Single column, condensed padding
Desktop (>1024px): Full two-column / sidebar layout
```

Key responsive rules:
- Left hero column on auth screens: `hidden lg:flex`
- Sidebar on dashboard: `hidden lg:flex` — mobile gets a slide-out drawer
- Metric cards: `grid-cols-2 lg:grid-cols-4`
- Chart height: `h-48 lg:h-64`

---

## 11. CSS Setup (`index.css`)

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

@theme {
  --font-sans: "Inter", ui-sans-serif, system-ui, sans-serif;
  --color-brand-gray: #1A1A1A;
  --color-surface: #1A1A1A;
  --color-surface-2: #242424;
}

@layer base {
  body {
    @apply font-sans bg-black text-white antialiased;
  }
  ::selection {
    @apply bg-white/30;
  }
}
```

---

## 12. Do Not List

- Do NOT use any color other than green/yellow/red for engagement states
- Do NOT add gradients or overlays on the auth screen hero video
- Do NOT use `border-radius: 0` anywhere — always at least `rounded-xl`
- Do NOT use colored brand accents (orange, purple, blue) for UI chrome
- Do NOT center-align body text blocks
- Do NOT use `font-bold` on body text — max `font-semibold` outside of metric numbers
- Do NOT use multiple font families — Inter only
- Do NOT use drop shadows on cards — rely on background color difference for depth
- Do NOT store or display student names or face images anywhere in the UI
- Do NOT use `localStorage` for sensitive data in production screens

---

## 13. Quick Reference — Tailwind Class Cheatsheet

```
Page bg:           bg-black
Card bg:           bg-[#1A1A1A]
Elevated card bg:  bg-[#242424]
Input bg:          bg-[#1A1A1A]

Primary text:      text-white
Secondary text:    text-white/60
Muted text:        text-white/30
Placeholder text:  text-white/20

Border default:    border-white/8
Border subtle:     border-white/5
Border focus:      ring-2 ring-white/20

Attentive color:   text-green-400  /  bg-green-500/15
Confused color:    text-yellow-400 /  bg-yellow-500/15
Distracted color:  text-red-400    /  bg-red-500/15

Heading:           text-3xl font-medium tracking-tight
Section title:     text-xl font-semibold tracking-tight
Body:              text-sm text-white/60 leading-relaxed
Caption:           text-xs text-white/30
Big metric:        text-5xl font-bold tracking-tight
```