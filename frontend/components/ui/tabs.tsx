"use client"

import { Tabs as TabsPrimitive } from "@base-ui/react/tabs"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

/**
 * Root Tabs container. Wraps `TabsList`, `TabsTrigger`, and `TabsContent`
 * to create a tabbed interface.
 *
 * @param props - All props from `@base-ui/react/tabs` `Root.Props`, plus:
 *   - `className` — Additional CSS classes applied to the root element.
 *   - `orientation` — Tab orientation: `"horizontal"` (default) or `"vertical"`.
 * @returns A `TabsPrimitive.Root` element with group styling and data attributes.
 * @example
 *   <Tabs defaultValue="account">
 *     <TabsList>
 *       <TabsTrigger value="account">Account</TabsTrigger>
 *       <TabsTrigger value="settings">Settings</TabsTrigger>
 *     </TabsList>
 *     <TabsContent value="account">Account content</TabsContent>
 *     <TabsContent value="settings">Settings content</TabsContent>
 *   </Tabs>
 */
function Tabs({
  className,
  orientation = "horizontal",
  ...props
}: TabsPrimitive.Root.Props) {
  return (
    <TabsPrimitive.Root
      data-slot="tabs"
      data-orientation={orientation}
      className={cn(
        "group/tabs flex gap-2 data-horizontal:flex-col",
        className
      )}
      {...props}
    />
  )
}

/**
 * Class-variance-authority variants for `TabsList` styling.
 *
 * Defines two visual variants:
 * - `default` — Rounded pill with muted background.
 * - `line` — Flat, transparent background with gap between triggers.
 *
 * @param options - Variant configuration object.
 * @param options.variant - The variant to apply: `"default"` or `"line"`.
 * @returns A merged class string with the selected variant's styles.
 */
const tabsListVariants = cva(
  "group/tabs-list inline-flex w-fit items-center justify-center rounded-lg p-[3px] text-muted-foreground group-data-horizontal/tabs:h-8 group-data-vertical/tabs:h-fit group-data-vertical/tabs:flex-col data-[variant=line]:rounded-none",
  {
    variants: {
      variant: {
        default: "bg-muted",
        line: "gap-1 bg-transparent",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

/**
 * Container for tab triggers. Renders a rounded pill or flat bar depending
 * on the `variant` prop.
 *
 * @param props - Combined props from `@base-ui/react/tabs` `List.Props` and:
 *   - `className` — Additional CSS classes applied to the list element.
 *   - `variant` — Visual style: `"default"` (rounded pill with background, default) or `"line"` (flat with gap).
 * @returns A `TabsPrimitive.List` element with variant-based styling.
 * @example
 *   <TabsList>
 *     <TabsTrigger value="a">Tab A</TabsTrigger>
 *     <TabsTrigger value="b">Tab B</TabsTrigger>
 *   </TabsList>
 */
function TabsList({
  className,
  variant = "default",
  ...props
}: TabsPrimitive.List.Props & VariantProps<typeof tabsListVariants>) {
  return (
    <TabsPrimitive.List
      data-slot="tabs-list"
      data-variant={variant}
      className={cn(tabsListVariants({ variant }), className)}
      {...props}
    />
  )
}

/**
 * Individual tab button that activates its associated `TabsContent` panel.
 *
 * @param props - All props from `@base-ui/react/tabs` `Tab.Props`, plus:
 *   - `className` — Additional CSS classes applied to the trigger element.
 * @returns A `TabsPrimitive.Tab` element with focus, hover, and active state styling.
 * @example
 *   <TabsTrigger value="account">Account</TabsTrigger>
 */
function TabsTrigger({ className, ...props }: TabsPrimitive.Tab.Props) {
  return (
    <TabsPrimitive.Tab
      data-slot="tabs-trigger"
      className={cn(
        "relative inline-flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-md border border-transparent px-1.5 py-0.5 text-sm font-medium whitespace-nowrap text-foreground/60 transition-all group-data-vertical/tabs:w-full group-data-vertical/tabs:justify-start hover:text-foreground focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50 focus-visible:outline-1 focus-visible:outline-ring disabled:pointer-events-none disabled:opacity-50 has-data-[icon=inline-end]:pr-1 has-data-[icon=inline-start]:pl-1 aria-disabled:pointer-events-none aria-disabled:opacity-50 dark:text-muted-foreground dark:hover:text-foreground group-data-[variant=default]/tabs-list:data-active:shadow-sm group-data-[variant=line]/tabs-list:data-active:shadow-none [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        "group-data-[variant=line]/tabs-list:bg-transparent group-data-[variant=line]/tabs-list:data-active:bg-transparent dark:group-data-[variant=line]/tabs-list:data-active:border-transparent dark:group-data-[variant=line]/tabs-list:data-active:bg-transparent",
        "data-active:bg-background data-active:text-foreground dark:data-active:border-input dark:data-active:bg-input/30 dark:data-active:text-foreground",
        "after:absolute after:bg-foreground after:opacity-0 after:transition-opacity group-data-horizontal/tabs:after:inset-x-0 group-data-horizontal/tabs:after:bottom-[-5px] group-data-horizontal/tabs:after:h-0.5 group-data-vertical/tabs:after:inset-y-0 group-data-vertical/tabs:after:-right-1 group-data-vertical/tabs:after:w-0.5 group-data-[variant=line]/tabs-list:data-active:after:opacity-100",
        className
      )}
      {...props}
    />
  )
}

/**
 * Content panel associated with a `TabsTrigger`. Only visible when its
 * matching trigger is active.
 *
 * @param props - All props from `@base-ui/react/tabs` `Panel.Props`, plus:
 *   - `className` — Additional CSS classes applied to the content panel.
 * @returns A `TabsPrimitive.Panel` element with flex layout and outline reset.
 * @example
 *   <TabsContent value="account">Account settings go here.</TabsContent>
 */
function TabsContent({ className, ...props }: TabsPrimitive.Panel.Props) {
  return (
    <TabsPrimitive.Panel
      data-slot="tabs-content"
      className={cn("flex-1 text-sm outline-none", className)}
      {...props}
    />
  )
}

export { Tabs, TabsList, TabsTrigger, TabsContent, tabsListVariants }
