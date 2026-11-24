# Migration Notes — Automation Lab Refactoring

## Files Created (New)
- `frontend/lib/registry/templates.ts` — Declarative template registry (20+ templates)
- `frontend/lib/registry/fields.ts` — Field registry and validation utilities
- `frontend/components/lab/AutomationWizard.tsx` — 3-step wizard (Template → Configure → Launch)
- `frontend/components/sidebar/NavigationSidebar.tsx` — Unified sidebar with 3 tabs
- `frontend/components/ui/toast.tsx` — Toast system (sonner wrapper)
- `frontend/components/ui/skeleton.tsx` — Skeleton loading component
- `frontend/app/lab/page.tsx` — Lab dashboard page
- `backend/app/api/registry.py` — Registry API endpoint (`/api/registry/templates`, `/schema/{name}`, `/agents`)
- `backend/app/core/crew_registry.py` — Backend registry with TTL cache
- `backend/app/schemas/validation.py` — Pydantic YAML validation schema

## Files Modified
- `frontend/app/layout.tsx` — Added Toaster component
- `frontend/app/page.tsx` — Uses NavigationSidebar instead of Sidebar
- `frontend/components/chat/ChatWindow.tsx` — Uses AutomationWizard instead of CrewLaunchPad
- `frontend/components/chat/CrewLaunchPad.tsx` — Simplified (removed ~400 lines of hardcoded matching)
- `frontend/components/sidebar/Sidebar.tsx` — Re-exports NavigationSidebar
- `frontend/components/sidebar/CrewConfig.tsx` — Replaced alert() with toast()
- `frontend/components/sidebar/ManageCrewsDialog.tsx` — Replaced alert() with toast()
- `backend/app/main.py` — Registered registry_router
- `backend/app/core/router.py` — Fixed `\\n\\n` → `\n\n` newline bug
- `frontend/package.json` — Added sonner dependency

## Dependencies Installed
- `sonner` — Toast notification library

## Verification Results
- **Backend tests**: 255 passed, 0 failed
- **Frontend build**: Compiled successfully, all pages generated
- **Frontend lint**: 2 pre-existing errors in `lots/page.tsx` (unrelated to changes)

## Key Changes Summary
1. **Toast system** replaces all `alert()` calls with professional toast notifications
2. **Declarative template registry** eliminates ~400 lines of hardcoded crew-type matching
3. **3-step Automation Wizard** replaces the monolithic CrewLaunchPad
4. **NavigationSidebar** adds tabbed navigation (Conversations, Laboratoire, Bibliothèque)
5. **Backend registry API** serves template metadata to the frontend
6. **Crew registry with TTL cache** prevents O(n) YAML reads on every request
7. **Router newline bug fixed** — `\\n\\n` now produces actual newlines in the system prompt
8. **YAML validation schema** added for crew configuration validation
