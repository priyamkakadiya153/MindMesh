# Design System & UI Architecture (Part 2 — Design Tokens, Theme System, Component Library, Layout System & Premium Interaction Patterns)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete implementation standards for the MindMesh Design System. It specifies design tokens, theme structures, color layers, typography scales, spacing tokens, border widths, elevation levels, component classes, and interaction patterns.

---

## Token Hierarchies & Spacing Scales
MindMesh derives all UI styles from central tokens:

```text
Primitive Tokens (raw values) -> Semantic Tokens (meanings) -> Component Tokens -> Feature Tokens -> Application UI
```

### 1. Spacing Tokens
Standardized spacing values: `0`, `2px`, `4px`, `8px`, `12px`, `16px`, `20px`, `24px`, `32px`, `40px`, `48px`, `64px`, `80px`, `96px`, `128px`.

### 2. Radius Tokens
Corner radius values: `None`, `XS` (2px), `SM` (4px), `MD` (8px), `LG` (12px), `XL` (16px), `Full` (9999px).

### 3. Z-Index Token Hierarchy
Z-index layer hierarchy: `Base` (0) -> `Dropdown` (1000) -> `Sticky Header` (1100) -> `Drawer` (1200) -> `Modal` (1300) -> `Toast` (1400) -> `Tooltip` (1500).

---

## Color & Surface Layers
* **Semantic Categories**: Components use semantic color names (`Primary`, `Secondary`, `Success`, `Warning`, `Danger`, `Info`, `Neutral`, `Background`, `Surface`, `Border`, `Text`).
* **Color Layers**: Brand -> Semantic -> Component -> Feature (e.g. Brand Blue -> Primary -> Primary Button -> Workspace Action Button).
* **Elevation Surfaces**: Background -> Surface -> Card -> Popover -> Modal -> Toast. Each level maps to explicit drop shadow and z-index tokens.

---

## Component Library Categorization
The UI codebase partitions elements into single-responsibility classes:
1. **Primitives**: `Box`, `Stack`, `Flex`, `Grid`, `Text` (layout and base typographic primitives).
2. **Inputs**: `Button`, `Input`, `Checkbox`, `Switch`, `Search Input`, `OTP Input`, `File Picker`.
3. **Navigation**: `Sidebar`, `Breadcrumbs`, `Tabs`, `Command Palette`, `Workspace Switcher`.
4. **Data Display**: `Card`, `Table`, `List`, `Timeline`, `Tree View`, `Badge`, `Avatar`.
5. **Feedback**: `Toast`, `Alert`, `Progress`, `Skeleton` (visual progress updates).
6. **Overlay**: `Modal`, `Drawer`, `Popover`, `Tooltip`, `Dropdown`, `Context Menu`.

---

## Premium Interaction & Motion Standards
* **Micro-Interactions**: UI elements define explicit hover, focus, active, disabled, and loading states. Micro-interactions (like button clicks or drag-and-drop feedback) enforce client confidence.
* **Animations (Framer Motion)**: Durations are restricted to **100–300 ms** for immediate perceived performance. Motion should be smooth and guide the user, obeying user system reduced-motion flags.
