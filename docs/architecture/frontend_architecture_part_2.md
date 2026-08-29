# Frontend Architecture (Part 2 — Component Architecture & Design System)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the official Component Architecture and Design System for MindMesh. The objective is to create a modern, professional, consistent, and scalable user interface that feels like a premium productivity platform.

Every component, page, layout, animation, and visual element must follow this document.

---

## UI Layer Architecture
MindMesh follows Atomic Design principles organized into four layers:

```text
Primitive Layer (Atoms) -> Shared Layer (Molecules) -> Feature Layer (Organisms) -> Page Layer (Templates/Pages)
```

1. **Primitive Layer (Atoms)**: Basic elements (Buttons, Inputs, Badges, Avatars, Icons, Dividers).
2. **Shared Layer (Molecules)**: Simple compositions (Search Bar, File Cards, User Cards).
3. **Feature Layer (Organisms)**: Complex UI modules (Chat Window, Semantic Search Panel, File Intelligence Panel).
4. **Page Layer (Pages)**: Full-page layout assemblies (Dashboard, Search, Conversations, Files).

---

## Design Tokens
All styling values must be centralized. Do not reference raw visual values directly inside components. Use semantic design tokens:

### 1. Typography Hierarchy
* Hierarchy: Display, Heading, Title, Subtitle, Body, Caption, Label.
* Rules: Consistent line heights, comfortable reading widths, and clean display weighting.

### 2. Color System
* Tokens: Primary, Secondary, Success, Warning, Error, Info, Background, Surface, Border, Text Primary, Text Secondary.

### 3. Spacing System
* Values are standardized on an 8pt grid scale: `4`, `8`, `12`, `16`, `20`, `24`, `32`, `40`, `48`, `64`.

### 4. Borders & Radius
* Standardized scales (Small, Medium, Large, Extra Large).

### 5. Elevation (Shadows)
* Standardized levels: None, Small, Medium, Large. Use sparingly.

---

## Icon Strategy
* Standardized library: **Lucide React**.
* Consistency: Maintain a uniform stroke width, shape, and color scheme throughout the application. Icons should support text labels rather than fully replace them.

---

## Motion Design
* Standardized library: **Framer Motion**.
* Triggers: Purposeful state changes (page transitions, drawer sliding, dialog openings, notification dismissals, list item additions).
* Constraint: Animations must be fast, smooth, and purposeful. Avoid excessive decorative animation.

---

## UI Performance & Loading States
* No blank screens are allowed during asynchronous tasks.
* Skeletons, progress indicators, empty states (explaining context and calls to action), and non-technical actionable error messages must be provided for all API request lifecycles.
