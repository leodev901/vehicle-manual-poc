# Design System Strategy: The Ethereal Assistant

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Curator."** 

We are moving away from the "industrial" look of traditional vehicle manuals and toward an experience that feels like a high-end concierge service. The system rejects the rigid, boxed-in layouts of legacy software in favor of **Soft Minimalism**. 

To break the "template" look, we utilize **intentional asymmetry** and **tonal depth**. The interface should feel less like a website and more like a physical object—a series of layered, frosted surfaces floating in a clean, airy environment. We use radical whitespace to signify premium quality, ensuring the user never feels overwhelmed by technical data.

---

## 2. Colors & Surface Logic
The palette is rooted in "Mint Breeze" and neutral tones, but its application is where the sophistication lies.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders to define sections. Traditional "dividers" are a sign of lazy architecture. Boundaries must be defined solely through:
- **Background Shifts:** Use `surface-container-low` sections sitting on a `surface` background.
- **Tonal Transitions:** Leveraging subtle shifts between `surface` and `surface-bright`.

### Surface Hierarchy & Nesting
Treat the UI as a series of physical layers. Use the `surface-container` tiers to create "nested" depth:
- **Level 0 (Base):** `surface` (#f8f9fa).
- **Level 1 (Sections):** `surface-container-low` (#f3f4f5).
- **Level 2 (Interactive Cards):** `surface-container-lowest` (#ffffff) to provide a "pop" of clean white against the gray base.

### The "Glass & Gradient" Rule
To elevate the AI chatbot experience, use **Glassmorphism** for floating elements (like the chat input bar or sticky headers). Use `surface` colors at 80% opacity with a `backdrop-blur: 20px`. 

### Signature Textures
Main CTAs and Hero states should utilize a **Signature Gradient**:
- **Start:** `primary` (#006b5b)
- **End:** `primary_container` (#4fdbc0)
- **Angle:** 135 degrees. This provides a "visual soul" that flat color cannot replicate.

---

## 3. Typography
We utilize a pairing of **Manrope** for high-impact editorial moments and **Inter** for functional clarity.

*   **Display & Headlines (Manrope):** These are the "editorial" voice. Use `display-lg` and `headline-md` with generous tracking (-0.02em) to create a sophisticated, thin, and modern look.
*   **Body & Titles (Inter):** Inter handles the heavy lifting of AI-generated text. It is chosen for its mathematical precision and high legibility at small sizes.
*   **Hierarchy Strategy:** Information density should be low. If a vehicle manual explanation is long, use `title-lg` for key takeaways and `body-md` for the granular details. Never allow text to feel "clumped."

---

## 4. Elevation & Depth
We eschew traditional "Drop Shadows" for **Ambient Occlusion** logic.

*   **The Layering Principle:** Place a `surface-container-lowest` card on a `surface-container-low` background. This creates a natural "lift" based on color theory rather than artificial shadows.
*   **Ambient Shadows:** When an element must float (e.g., a modal or a floating action button), use a diffuse shadow:
    *   `box-shadow: 0 20px 40px rgba(25, 28, 29, 0.05);` (A 5% tint of `on_surface`).
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, use the `outline_variant` token at **15% opacity**. Never use 100% opaque borders.
*   **Roundedness:** Adhere to the `xl` (3rem) for large containers and `DEFAULT` (1rem) for components. High corner radii communicate "approachability" and "high-tech soft goods."

---

## 5. Components

### The Chat Interface (Core Component)
- **User Bubbles:** Use `primary` background with `on_primary` text. Apply `border-radius: 1.5rem` with a sharp corner on the bottom right (`0.25rem`).
- **AI Bubbles:** `surface-container-highest` background. No border. Apply `border-radius: 1.5rem` with a sharp corner on the bottom left.
- **Input Field:** A floating `surface-container-lowest` pill with a `glassmorphism` backdrop blur. Use the `full` (9999px) border-radius.

### Buttons
- **Primary:** Gradient-filled (Mint Breeze to Mint Container). `radius-full`. No shadow, unless hovered.
- **Secondary:** `surface-container-high` background. `on_surface` text.
- **Tertiary:** Transparent background with `primary` text. Use for low-priority actions like "View Source."

### Interactive Vehicle Chips
- For selecting vehicle parts (e.g., "Engine," "Tires").
- **State:** Unselected = `surface-container-low`. Selected = `primary` with `on_primary` text.

### Cards & Lists
- **Rule:** Forbid divider lines.
- **Execution:** Separate "Engine Oil Status" from "Tire Pressure" using a `32px` vertical gap or by placing them in separate `surface-container-lowest` cards on a `surface-container-low` track.

---

## 6. Do’s and Don’ts

### Do:
*   **Do** use extreme whitespace. If you think there is enough space, add 16px more.
*   **Do** use "Mint Breeze" (`primary`) sparingly as an accent to guide the eye to the "Solve" button.
*   **Do** ensure all AI-generated text has a line-height of at least 1.6 to maintain the "editorial" feel.

### Don’t:
*   **Don't** use pure black (#000000). Use `on_surface` (#191c1d) for text to maintain the "soft" vibe.
*   **Don't** use standard "Material Design" cards with heavy shadows and 4px corners. It breaks the "App-like" premium feel.
*   **Don't** use icons with varying line weights. Use a thin-weight (200 or 300) icon set to match the sophisticated typography.