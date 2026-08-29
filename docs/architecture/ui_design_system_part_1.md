# Design System & UI Architecture (Part 1 — Design Philosophy, Visual Identity, Component System & User Experience Standards)

**Document Version:** 1.0
**Project:** MindMesh – AI-Powered Knowledge Intelligence System

---

## Purpose
This document defines the complete Design System and User Experience Architecture of MindMesh. It establishes visual identity principles, responsive grids, standard spacing scales, typography hierarchies, color surface rules, and premium micro-interaction parameters.

Every frontend page and React component must comply with this document.

---

## Design Personality & Visual Language
MindMesh is designed as a calm, technical, and premium **Live Knowledge Workspace** (drawing UX inspiration from platforms like Notion, Linear, Figma, Arc, and Raycast):
* **Spaciousness**: Layouts prioritize generous margins, clear hierarchy, and intentional whitespace to minimize cognitive load.
* **Semantic Meaning**: Visual elements and color schemes communicate actions, priorities, and status updates (avoiding arbitrary decorative visuals).

---

## Responsive Layouts & Spacing

### 1. Responsive Grids
Layout templates must adjust to viewport scales:
* **Desktop Viewports**: 12-column grid
* **Tablet Viewports**: 8-column grid
* **Mobile Viewports**: 4-column grid

### 2. Spacing Scale
All layout margins, paddings, and column gap specifications follow a strict 8pt grid scale:
`4px`, `8px`, `12px`, `16px`, `24px`, `32px`, `48px`, `64px`, `96px`.

---

## Typography & Layer Surfaces

### 1. Typography Scales
* Hierarchy scale: Display, Heading XL, Heading L, Heading M, Heading S, Body Large, Body, Body Small, Caption.
* Readability: Clean sans-serif typefaces (e.g. Outfit, Inter) providing excellent code block and multilingual support.

### 2. Surface Layer depth
UI depth is structured hierarchically:

```text
Background Layer (Base) -> Surface (Card Panels) -> Elevated Surface (Dropdowns) -> Floating Surface (Popovers) -> Modal Layer (Dialogs)
```

---

## Component Standards & Accessibility (WCAG 2.2 AA)
* **Status Loaders**: Spinner blocks are discouraged. Skeletons, progressive asset loading, and inline upload progress feeds are preferred.
* **Accessibility**: Keyboard navigation support (`Tab`, `Shift+Tab`, focus indicator loops within modals), custom outlines, and descriptive ARIA labels are core requirements.
* **Dark & Light Modes**: Both themes share the same component code and derive styles exclusively from semantic color tokens.
