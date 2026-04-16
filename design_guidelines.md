{
  "design_system_name": "Redline Studio — YouTube Automation Dashboard",
  "product_summary": {
    "app_type": "SaaS dashboard",
    "audience": "Spanish/bilingual YouTube creators automating kids content (Roblox clips, cartoons, curiosities)",
    "brand_attributes": [
      "professional",
      "clean",
      "high-signal data UI",
      "energetic (kids vibe) without looking childish",
      "trustworthy (automation + OAuth + compliance)"
    ],
    "north_star_actions": [
      "Create a new automation job",
      "Monitor pipeline progress in real time",
      "Review run artifacts + logs",
      "Tune templates/voices",
      "Track channel analytics",
      "Configure OAuth/API keys + schedule safely"
    ]
  },

  "visual_personality": {
    "style_fusion": [
      "SaaS dark dashboard density (Stripe/Mixpanel-like)",
      "YouTube Studio clarity (red accent + status emphasis)",
      "Roblox-inspired soft geometry + playful micro-accents (stickers/badges)"
    ],
    "layout_principles": {
      "primary": "Bento grid + card layout",
      "secondary": "F-pattern reading flow; left sidebar + top utility bar",
      "density": "High information density with generous spacing (2–3x more than default)"
    },
    "texture": {
      "rule": "Use subtle noise/grain overlays on large backgrounds only (not on cards).",
      "implementation": "Add a pseudo-element on the app shell with opacity 0.04–0.06 and mix-blend-mode: overlay."
    }
  },

  "typography": {
    "google_fonts": {
      "heading": {
        "family": "Space Grotesk",
        "weights": ["500", "600", "700"],
        "usage": "Navigation, page titles, KPI numbers"
      },
      "body": {
        "family": "Figtree",
        "weights": ["400", "500", "600"],
        "usage": "Tables, forms, helper text, logs"
      },
      "mono": {
        "family": "IBM Plex Mono",
        "weights": ["400", "500"],
        "usage": "Run logs, code-like artifacts, IDs"
      }
    },
    "tailwind_font_setup": {
      "note": "Main agent should add these to index.html (Google Fonts) and extend tailwind.config.js fontFamily.",
      "font_family_tokens": {
        "--font-heading": "Space Grotesk",
        "--font-body": "Figtree",
        "--font-mono": "IBM Plex Mono"
      }
    },
    "type_scale": {
      "h1": "text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight",
      "h2": "text-base md:text-lg text-muted-foreground",
      "section_title": "text-sm font-semibold tracking-wide uppercase",
      "kpi_number": "text-2xl md:text-3xl font-semibold tabular-nums",
      "body": "text-sm md:text-base",
      "small": "text-xs text-muted-foreground",
      "mono": "font-mono text-xs leading-relaxed"
    }
  },

  "color_system": {
    "mode": "dark-first",
    "notes": [
      "YouTube red (#FF0000) is the primary accent.",
      "Avoid purple gradients. Keep gradients mild and under 20% viewport.",
      "Use solid surfaces for reading areas (tables/logs/forms)."
    ],
    "tokens_hsl_for_shadcn": {
      "app": {
        "--background": "225 15% 6%",
        "--foreground": "210 20% 98%",
        "--card": "225 14% 9%",
        "--card-foreground": "210 20% 98%",
        "--popover": "225 14% 9%",
        "--popover-foreground": "210 20% 98%",
        "--muted": "225 12% 14%",
        "--muted-foreground": "215 14% 70%",
        "--border": "225 12% 18%",
        "--input": "225 12% 18%",
        "--ring": "0 100% 55%",
        "--radius": "0.75rem"
      },
      "brand": {
        "--primary": "0 100% 50%",
        "--primary-foreground": "0 0% 100%",
        "--secondary": "225 12% 14%",
        "--secondary-foreground": "210 20% 98%",
        "--accent": "210 90% 55%",
        "--accent-foreground": "225 15% 8%",
        "--destructive": "0 84% 60%",
        "--destructive-foreground": "0 0% 100%"
      },
      "status": {
        "--status-success": "142 72% 45%",
        "--status-running": "210 90% 55%",
        "--status-failed": "0 84% 60%",
        "--status-pending": "45 93% 55%",
        "--status-idle": "215 14% 70%"
      },
      "charts": {
        "--chart-1": "0 100% 50%",
        "--chart-2": "210 90% 55%",
        "--chart-3": "142 72% 45%",
        "--chart-4": "45 93% 55%",
        "--chart-5": "190 85% 45%"
      }
    },
    "hex_palette_reference": {
      "bg": "#0B0D12",
      "surface": "#121624",
      "surface_2": "#171C2E",
      "text": "#F5F7FF",
      "muted_text": "#AAB2C5",
      "border": "#242B3F",
      "youtube_red": "#FF0000",
      "electric_blue": "#2EA8FF",
      "mint_success": "#2ED47A",
      "amber_pending": "#FFCC33",
      "danger": "#FF4D4F"
    },
    "allowed_gradients": {
      "rule": "Only for hero/header background accents; max 20% viewport; never on cards/tables/logs.",
      "gradients": [
        {
          "name": "header-glow",
          "css": "radial-gradient(900px circle at 20% -10%, rgba(255,0,0,0.22), transparent 55%), radial-gradient(700px circle at 85% 0%, rgba(46,168,255,0.18), transparent 52%)"
        }
      ]
    }
  },

  "spacing_grid": {
    "container": {
      "max_width": "max-w-7xl",
      "page_padding": "px-4 sm:px-6 lg:px-8",
      "section_gap": "space-y-6 md:space-y-8"
    },
    "dashboard_grid": {
      "kpi": "grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4",
      "main": "grid grid-cols-1 xl:grid-cols-12 gap-4",
      "left_col": "xl:col-span-8",
      "right_col": "xl:col-span-4"
    },
    "touch_targets": "min-h-10 min-w-10 (44px preferred)"
  },

  "components": {
    "component_path": {
      "layout": {
        "sidebar": "/app/frontend/src/components/ui/collapsible.jsx (for collapsible nav groups)",
        "sheet_mobile_nav": "/app/frontend/src/components/ui/sheet.jsx",
        "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
        "separator": "/app/frontend/src/components/ui/separator.jsx",
        "resizable": "/app/frontend/src/components/ui/resizable.jsx (optional for desktop split panes: logs/artifacts)"
      },
      "core": {
        "button": "/app/frontend/src/components/ui/button.jsx",
        "badge": "/app/frontend/src/components/ui/badge.jsx",
        "card": "/app/frontend/src/components/ui/card.jsx",
        "tabs": "/app/frontend/src/components/ui/tabs.jsx",
        "table": "/app/frontend/src/components/ui/table.jsx",
        "progress": "/app/frontend/src/components/ui/progress.jsx",
        "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
        "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
        "dropdown": "/app/frontend/src/components/ui/dropdown-menu.jsx",
        "dialog": "/app/frontend/src/components/ui/dialog.jsx",
        "drawer": "/app/frontend/src/components/ui/drawer.jsx",
        "form": "/app/frontend/src/components/ui/form.jsx",
        "input": "/app/frontend/src/components/ui/input.jsx",
        "textarea": "/app/frontend/src/components/ui/textarea.jsx",
        "select": "/app/frontend/src/components/ui/select.jsx",
        "switch": "/app/frontend/src/components/ui/switch.jsx",
        "slider": "/app/frontend/src/components/ui/slider.jsx",
        "calendar": "/app/frontend/src/components/ui/calendar.jsx",
        "sonner_toast": "/app/frontend/src/components/ui/sonner.jsx"
      }
    },

    "button_system": {
      "tone": "Professional/corporate with energetic accent",
      "shape": "Rounded 10–12px (use --radius 0.75rem)",
      "variants": {
        "primary": {
          "use": "Main CTAs: Run pipeline, Add job, Upload",
          "tailwind": "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:bg-red-600 focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))]",
          "micro_interaction": "On hover: subtle lift (translateY -1px) + glow shadow; on press: scale 0.98"
        },
        "secondary": {
          "use": "Secondary actions: Preview, Duplicate template",
          "tailwind": "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))] hover:bg-[hsl(var(--muted))] border border-[hsl(var(--border))]"
        },
        "ghost": {
          "use": "Toolbar icon buttons",
          "tailwind": "hover:bg-white/5 text-[hsl(var(--foreground))]"
        },
        "danger": {
          "use": "Delete job, revoke token",
          "tailwind": "bg-[hsl(var(--destructive))] text-[hsl(var(--destructive-foreground))] hover:bg-red-500"
        }
      },
      "data_testid_examples": [
        "data-testid=\"queue-add-job-button\"",
        "data-testid=\"pipeline-run-button\"",
        "data-testid=\"settings-save-button\""
      ]
    },

    "status_badges": {
      "use_component": "Badge",
      "mapping": [
        {
          "status": "success",
          "classes": "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30"
        },
        {
          "status": "running",
          "classes": "bg-sky-500/15 text-sky-300 border border-sky-500/30"
        },
        {
          "status": "failed",
          "classes": "bg-red-500/15 text-red-300 border border-red-500/30"
        },
        {
          "status": "pending",
          "classes": "bg-amber-400/15 text-amber-200 border border-amber-400/30"
        },
        {
          "status": "idle",
          "classes": "bg-white/5 text-[hsl(var(--muted-foreground))] border border-[hsl(var(--border))]"
        }
      ],
      "coppa_indicator": {
        "label": "COPPA",
        "classes": "bg-fuchsia-500/10 text-fuchsia-200 border border-fuchsia-500/25",
        "note": "COPPA is informational; keep it subtle but always visible on job rows/cards."
      }
    },

    "cards": {
      "base_classes": "bg-[hsl(var(--card))] text-[hsl(var(--card-foreground))] border border-[hsl(var(--border))] rounded-[var(--radius)] shadow-[0_10px_30px_rgba(0,0,0,0.35)]",
      "header": "flex items-start justify-between gap-3",
      "kpi_card": {
        "layout": "Icon chip + label + big number + delta",
        "icon_chip": "h-10 w-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center",
        "delta_positive": "text-emerald-300",
        "delta_negative": "text-red-300"
      }
    },

    "tables": {
      "use_component": "Table",
      "row_hover": "hover:bg-white/3",
      "sticky_header": "sticky top-0 bg-[hsl(var(--card))]",
      "density": "Use text-sm, py-3, and truncate for long IDs",
      "empty_state": "Use Skeleton + a centered Card with CTA (Add job / Create template)"
    },

    "pipeline_visualization": {
      "layout": "Horizontal stepper on desktop; vertical timeline on mobile",
      "components": ["Card", "Progress", "Badge", "Tabs", "ScrollArea"],
      "step_node": {
        "classes": "relative flex items-center gap-3 p-3 rounded-xl border border-[hsl(var(--border))] bg-white/3",
        "state_styles": {
          "idle": "opacity-70",
          "running": "ring-1 ring-sky-500/40 shadow-[0_0_0_1px_rgba(46,168,255,0.25)]",
          "success": "ring-1 ring-emerald-500/35",
          "failed": "ring-1 ring-red-500/35"
        }
      },
      "real_time_logs_panel": {
        "recommendation": "Split view: left pipeline steps, right logs/artifacts. On mobile, use Tabs: Logs | Artifacts.",
        "log_style": "Use mono font, line numbers, and severity chips (info/warn/error)."
      }
    },

    "charts_analytics": {
      "library": "Recharts (already available)",
      "chart_container": "Card with padded header + legend row",
      "styling": {
        "grid": "stroke: rgba(255,255,255,0.08)",
        "axis": "tick: rgba(170,178,197,0.9)",
        "line_primary": "stroke: #FF0000",
        "line_secondary": "stroke: #2EA8FF",
        "area_fill": "Use solid fill with low opacity (0.12–0.18), not gradients"
      },
      "recommended_charts": [
        "Views over time (LineChart)",
        "Watch time (AreaChart)",
        "Top videos (BarChart)",
        "Language split ES/EN (PieChart with 2 slices)"
      ]
    },

    "forms_settings": {
      "pattern": "Two-column settings on desktop; single column on mobile",
      "sections": [
        "YouTube OAuth",
        "API keys",
        "Posting schedule",
        "Anti-detection",
        "COPPA defaults",
        "GitHub Actions"
      ],
      "anti_detection_panel": {
        "tone": "Serious + caution",
        "ui": "Use Alert component with neutral warning copy; use Switch + Slider; add Tooltip for each risky option",
        "example_controls": [
          "Switch: Randomize upload time ±X minutes",
          "Slider: Human-like pauses (0–10s)",
          "Select: Proxy profile",
          "Textarea: Custom user-agent list"
        ]
      }
    },

    "navigation": {
      "sidebar": {
        "desktop": "Collapsible sidebar with grouped sections: Overview, Automation, Library, Insights, Admin",
        "mobile": "Use Sheet for slide-over nav",
        "active_item": "bg-white/5 border border-white/10 + left accent bar (2px) in YouTube red",
        "hover": "bg-white/3",
        "collapse": "Icon-only mode at ~72px width; show tooltips"
      },
      "topbar": {
        "elements": [
          "Global search (Command component)",
          "Create button",
          "Notifications",
          "Language toggle ES/EN",
          "Profile menu"
        ]
      }
    }
  },

  "motion_microinteractions": {
    "library": {
      "recommended": "framer-motion",
      "install": "npm i framer-motion",
      "usage": "Use for page transitions, pipeline step pulses, and toast entrance. Keep durations short."
    },
    "principles": {
      "durations": {
        "fast": "120–160ms",
        "base": "180–220ms",
        "slow": "260–320ms"
      },
      "easing": "cubic-bezier(0.2, 0.8, 0.2, 1)",
      "hover": "Buttons/cards: translateY(-1px) + shadow increase; never transition: all",
      "running_state": "Pipeline running step: subtle pulse ring (opacity animation)"
    },
    "scroll": {
      "pattern": "Sticky section headers in tables/logs; subtle shadow appears when scrolled"
    }
  },

  "accessibility": {
    "contrast": "Ensure WCAG AA for text on dark surfaces; avoid low-contrast gray-on-gray.",
    "focus": "Always visible focus ring: focus-visible:ring-2 focus-visible:ring-[hsl(var(--ring))] focus-visible:ring-offset-0",
    "reduced_motion": "Respect prefers-reduced-motion: disable pulsing animations and heavy transitions",
    "keyboard": "All menus/dialogs/tabs must be keyboard navigable (shadcn defaults help)"
  },

  "data_testid_policy": {
    "rule": "All interactive and key informational elements MUST include data-testid.",
    "naming": "kebab-case describing role (not appearance)",
    "examples": [
      "data-testid=\"sidebar-nav-queue-link\"",
      "data-testid=\"dashboard-quota-meter\"",
      "data-testid=\"pipeline-step-tts-status\"",
      "data-testid=\"history-run-logs-open-button\"",
      "data-testid=\"templates-create-template-button\"",
      "data-testid=\"settings-youtube-oauth-connect-button\""
    ]
  },

  "page_blueprints": {
    "dashboard": {
      "route": "/",
      "sections": [
        "Header glow background (decorative only)",
        "KPI bento grid (quota usage, videos uploaded, success rate, channel subs)",
        "Pipeline status card (current job + stepper)",
        "Recent runs table (last 10) with status badges + COPPA chip",
        "Right rail: Quick actions + Template spotlight"
      ]
    },
    "queue": {
      "route": "/queue",
      "sections": [
        "Queue table with priority + status + COPPA",
        "Add job (Dialog/Drawer on mobile)",
        "Bulk actions (pause/resume/cancel)"
      ]
    },
    "pipeline": {
      "route": "/pipeline",
      "sections": [
        "Pipeline runner stepper",
        "Real-time logs (ScrollArea) + artifacts",
        "Retry failed step + download artifacts"
      ]
    },
    "history": {
      "route": "/history",
      "sections": [
        "Run history table",
        "Logs modal (Dialog) with severity filters",
        "Artifacts list (script, audio, video, thumbnail)"
      ]
    },
    "templates": {
      "route": "/templates",
      "sections": [
        "Template cards grid",
        "Create/edit template (Dialog)",
        "Voice presets + bilingual hooks"
      ]
    },
    "analytics": {
      "route": "/analytics",
      "sections": [
        "Date range (Calendar popover)",
        "Charts (views, watch time, subs)",
        "Top videos table",
        "ES/EN split"
      ]
    },
    "settings": {
      "route": "/settings",
      "sections": [
        "OAuth connect + token status",
        "API keys",
        "Posting schedule",
        "Anti-detection panel (Alert + Switch/Slider)",
        "GitHub Actions integration"
      ]
    }
  },

  "image_urls": {
    "hero_header_background_optional": [
      {
        "url": "https://images.unsplash.com/photo-1619025278360-af95dcc48a66?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTV8MHwxfHNlYXJjaHwzfHx5b3V0dWJlJTIwc3R1ZGlvJTIwc2V0dXAlMjBuZW9ufGVufDB8fHxibHVlfDE3NzYzNDIyNTZ8MA&ixlib=rb-4.1.0&q=85",
        "category": "decorative",
        "description": "Neon studio texture for a blurred header background (use as low-opacity overlay, not as content)."
      }
    ],
    "empty_state_illustration_optional": [
      {
        "url": "https://images.unsplash.com/photo-1652512456007-e16ac46f1879?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2OTV8MHwxfHNlYXJjaHwxfHx5b3V0dWJlJTIwc3R1ZGlvJTIwc2V0dXAlMjBuZW9ufGVufDB8fHxibHVlfDE3NzYzNDIyNTZ8MA&ixlib=rb-4.1.0&q=85",
        "category": "empty-state",
        "description": "Desk setup image for empty states (Queue empty / No templates). Use grayscale + 10% opacity behind copy."
      }
    ],
    "templates_cover_optional": [
      {
        "url": "https://images.unsplash.com/photo-1646809021377-6fe5ba140b4a?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzZ8MHwxfHNlYXJjaHwyfHxraWRzJTIwY29udGVudCUyMGNyZWF0b3IlMjBzdHVkaW8lMjBkYXJrJTIwZGVza3xlbnwwfHx8cmVkfDE3NzYzNDIyNTN8MA&ixlib=rb-4.1.0&q=85",
        "category": "templates",
        "description": "Playful desk flatlay for template cards (blurred + cropped)."
      }
    ]
  },

  "implementation_notes_for_js": {
    "icons": {
      "library": "lucide-react",
      "usage": "Use icons for sidebar + status chips; avoid emoji icons."
    },
    "app_css_cleanup": {
      "note": "Remove/avoid centered App-header styles from App.css; rely on Tailwind + tokens in index.css."
    },
    "global_shell_classes": {
      "app_shell": "min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]",
      "header_glow": "relative overflow-hidden before:absolute before:inset-0 before:bg-[radial-gradient(900px_circle_at_20%_-10%,rgba(255,0,0,0.22),transparent_55%),radial-gradient(700px_circle_at_85%_0%,rgba(46,168,255,0.18),transparent_52%)] before:pointer-events-none"
    },
    "realtime_ui": {
      "pattern": "Use optimistic UI + polling/WebSocket; show Skeleton while loading; show Progress for step completion."
    }
  },

  "instructions_to_main_agent": [
    "Update /app/frontend/src/index.css tokens: keep shadcn structure but set .dark variables to the provided HSL tokens (dark-first).",
    "Ensure the app root has className=\"dark\" (or toggle) so the dark theme is active by default.",
    "Do NOT use App.css centered layout; remove App-header flex centering patterns.",
    "Use shadcn/ui components from /src/components/ui only (Button, Card, Badge, Table, Tabs, Dialog, Sheet, ScrollArea, Progress, Calendar, Sonner).",
    "Implement sidebar + topbar shell: Sidebar collapsible on desktop; Sheet on mobile.",
    "Pipeline page: stepper + logs split view (Resizables on desktop; Tabs on mobile).",
    "Analytics: Recharts with solid low-opacity fills (no gradients).",
    "Add data-testid to every interactive element and key info display (quota meter, statuses, run IDs, etc.).",
    "Install framer-motion for micro-interactions and running-state pulses; respect prefers-reduced-motion.",
    "Use lucide-react icons; no emoji icons.",
    "Status badges must follow the provided color mapping (success/running/failed/pending/idle) and always show COPPA chip on jobs."
  ],

  "general_ui_ux_design_guidelines": [
    "You must not apply universal transition. Eg: transition: all. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms",
    "You must not center align the app container, ie do not add .App { text-align: center; } in the css file. This disrupts the human natural reading flow of text",
    "NEVER: use AI assistant Emoji characters like 🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use FontAwesome cdn or lucid-react library already installed in the package.json",
    "GRADIENT RESTRICTION RULE: NEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element. Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc",
    "NEVER use dark gradients for logo, testimonial, footer etc",
    "NEVER let gradients cover more than 20% of the viewport.",
    "NEVER apply gradients to text-heavy content or reading areas.",
    "NEVER use gradients on small UI elements (<100px width).",
    "NEVER stack multiple gradient layers in the same viewport.",
    "ENFORCEMENT RULE: Id gradient area exceeds 20% of viewport OR affects readability, THEN use solid colors",
    "How and where to use: Section backgrounds (not content backgrounds); Hero section header content; Decorative overlays and accent elements only; Hero section with 2-3 mild color; Gradients creation can be done for any angle say horizontal, vertical or diagonal",
    "For AI chat, voice application, do not use purple color. Use color like light green, ocean blue, peach orange etc",
    "Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead.",
    "Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.",
    "Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.",
    "Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly",
    "Component Reuse: Prioritize using pre-existing components from src/components/ui when applicable; Create new components that match the style and conventions of existing components when needed; Examine existing components to understand the project's component patterns before creating new ones",
    "IMPORTANT: Do not use HTML based component like dropdown, calendar, toast etc. You MUST always use /app/frontend/src/components/ui/ only as a primary components as these are modern and stylish component",
    "Best Practices: Use Shadcn/UI as the primary component library for consistency and accessibility; Import path: ./components/[component-name]",
    "Export Conventions: Components MUST use named exports (export const ComponentName = ...); Pages MUST use default exports (export default function PageName() {...})",
    "Toasts: Use sonner for toasts; Sonner component are located in /app/src/components/ui/sonner.tsx",
    "Use 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals."
  ]
}
