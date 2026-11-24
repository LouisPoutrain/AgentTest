"use client"

import * as React from "react"
import { Select as SelectPrimitive } from "@base-ui/react/select"

import { cn } from "@/lib/utils"
import { ChevronDownIcon, CheckIcon, ChevronUpIcon } from "lucide-react"

/**
 * The root Select component that groups all select parts.
 *
 * Wraps `SelectPrimitive.Root` and exposes it as a named export.
 * Does not render its own HTML element; it is a logical container
 * for `SelectTrigger`, `SelectContent`, `SelectGroup`, etc.
 *
 * @example
 * ```tsx
 * <Select value={font} onValueChange={setFont}>
 *   <SelectTrigger size="default">
 *     <SelectValue />
 *   </SelectTrigger>
 *   <SelectContent>
 *     <SelectItem value="sans">Sans-serif</SelectItem>
 *     <SelectItem value="serif">Serif</SelectItem>
 *     <SelectItem value="mono">Monospace</SelectItem>
 *   </SelectContent>
 * </Select>
 * ```
 */
const Select = SelectPrimitive.Root

/**
 * A group container for related `SelectItem` elements.
 *
 * Renders a `<div>` element with `data-slot="select-group"`.
 * Typically used to wrap a set of items that belong together.
 *
 * @param className - Additional CSS classes applied to the group container.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Group`.
 * @returns A grouped select region containing child items.
 */
function SelectGroup({ className, ...props }: SelectPrimitive.Group.Props) {
  return (
    <SelectPrimitive.Group
      data-slot="select-group"
      className={cn("scroll-my-1 p-1", className)}
      {...props}
    />
  )
}

/**
 * Displays the currently selected item's value or label inside the trigger.
 *
 * Renders a `<span>` element with `data-slot="select-value"`.
 * When the parent `Select` has an `items` prop, it renders the label
 * of the selected item. Without `items`, it renders the raw value.
 *
 * @param className - Additional CSS classes applied to the value span.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Value`.
 * @returns A span showing the selected value, styled with left-aligned text.
 *
 * @example
 * ```tsx
 * <SelectTrigger>
 *   <SelectValue placeholder="Choose an option..." />
 * </SelectTrigger>
 * ```
 */
function SelectValue({ className, ...props }: SelectPrimitive.Value.Props) {
  return (
    <SelectPrimitive.Value
      data-slot="select-value"
      className={cn("flex flex-1 text-left", className)}
      {...props}
    />
  )
}

/**
 * The button that opens the select popup.
 *
 * Renders a `<button>` element with `data-slot="select-trigger"`.
 * Supports two sizes (`"sm"` and `"default"`) and applies focus,
 * disabled, and placeholder styling automatically. Includes a chevron
 * icon that indicates the dropdown state.
 *
 * @param className - Additional CSS classes applied to the trigger button.
 * @param size - Visual size of the trigger. `"sm"` is 28px tall, `"default"` is 32px.
 * @param children - Content rendered inside the trigger (typically `SelectValue`).
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Trigger`.
 * @returns A styled trigger button that opens the select popup on click or keyboard.
 *
 * @example
 * ```tsx
 * <SelectTrigger size="sm" className="w-40">
 *   <SelectValue placeholder="Select..." />
 * </SelectTrigger>
 * ```
 */
function SelectTrigger({
  className,
  size = "default",
  children,
  ...props
}: SelectPrimitive.Trigger.Props & {
  size?: "sm" | "default"
}) {
  return (
    <SelectPrimitive.Trigger
      data-slot="select-trigger"
      data-size={size}
      className={cn(
        "flex w-fit items-center justify-between gap-1.5 rounded-lg border border-input bg-transparent py-2 pr-2 pl-2.5 text-sm whitespace-nowrap transition-colors outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:cursor-not-allowed disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 data-placeholder:text-muted-foreground data-[size=default]:h-8 data-[size=sm]:h-7 data-[size=sm]:rounded-[min(var(--radius-md),10px)] *:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-1.5 dark:bg-input/30 dark:hover:bg-input/50 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      {children}
      <SelectPrimitive.Icon
        render={
          <ChevronDownIcon className="pointer-events-none size-4 text-muted-foreground" />
        }
      />
    </SelectPrimitive.Trigger>
  )
}

/**
 * The floating popup that contains the list of select items.
 *
 * Renders a portal with a positioner and the popup `<div>`. Handles
 * positioning relative to the trigger, scroll arrows, and open/close
 * animations. The popup is scrollable and matches the trigger width.
 *
 * @param className - Additional CSS classes applied to the popup element.
 * @param children - The list of items and optional labels to render inside the popup.
 * @param side - Which side of the trigger to position the popup. Defaults to `"bottom"`.
 * @param sideOffset - Distance in pixels between the trigger and the popup. Defaults to `4`.
 * @param align - Horizontal alignment of the popup relative to the trigger. Defaults to `"center"`.
 * @param alignOffset - Additional offset in pixels along the alignment axis. Defaults to `0`.
 * @param alignItemWithTrigger - Whether to overlap the popup with the trigger for text alignment. Defaults to `true`.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Popup`.
 * @returns A positioned floating popup containing select items with scroll arrows.
 *
 * @example
 * ```tsx
 * <SelectContent side="bottom" align="start">
 *   <SelectItem value="a">Option A</SelectItem>
 *   <SelectItem value="b">Option B</SelectItem>
 * </SelectContent>
 * ```
 */
function SelectContent({
  className,
  children,
  side = "bottom",
  sideOffset = 4,
  align = "center",
  alignOffset = 0,
  alignItemWithTrigger = true,
  ...props
}: SelectPrimitive.Popup.Props &
  Pick<
    SelectPrimitive.Positioner.Props,
    "align" | "alignOffset" | "side" | "sideOffset" | "alignItemWithTrigger"
  >) {
  return (
    <SelectPrimitive.Portal>
      <SelectPrimitive.Positioner
        side={side}
        sideOffset={sideOffset}
        align={align}
        alignOffset={alignOffset}
        alignItemWithTrigger={alignItemWithTrigger}
        className="isolate z-50"
      >
        <SelectPrimitive.Popup
          data-slot="select-content"
          data-align-trigger={alignItemWithTrigger}
          className={cn("relative isolate z-50 max-h-(--available-height) w-(--anchor-width) min-w-36 origin-(--transform-origin) overflow-x-hidden overflow-y-auto rounded-lg bg-popover text-popover-foreground shadow-md ring-1 ring-foreground/10 duration-100 data-[align-trigger=true]:animate-none data-[side=bottom]:slide-in-from-top-2 data-[side=inline-end]:slide-in-from-left-2 data-[side=inline-start]:slide-in-from-right-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95", className )}
          {...props}
        >
          <SelectScrollUpButton />
          <SelectPrimitive.List>{children}</SelectPrimitive.List>
          <SelectScrollDownButton />
        </SelectPrimitive.Popup>
      </SelectPrimitive.Positioner>
    </SelectPrimitive.Portal>
  )
}

/**
 * An accessible label for a group of select items.
 *
 * Renders a `<div>` element with `data-slot="select-label"`.
 * The label is visually styled as muted, small text and is
 * not selectable as an item.
 *
 * @param className - Additional CSS classes applied to the label element.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.GroupLabel`.
 * @returns A non-interactive label div for a select group.
 *
 * @example
 * ```tsx
 * <SelectContent>
 *   <SelectGroup>
 *     <SelectLabel>Font Family</SelectLabel>
 *     <SelectItem value="sans">Sans</SelectItem>
 *   </SelectGroup>
 * </SelectContent>
 * ```
 */
function SelectLabel({
  className,
  ...props
}: SelectPrimitive.GroupLabel.Props) {
  return (
    <SelectPrimitive.GroupLabel
      data-slot="select-label"
      className={cn("px-1.5 py-1 text-xs text-muted-foreground", className)}
      {...props}
    />
  )
}

/**
 * An individual selectable option within the select popup.
 *
 * Renders a `<div>` element with `data-slot="select-item"`. Displays
 * the item text with a check indicator when selected. Supports disabled
 * state and applies focus/hover styling automatically.
 *
 * @param className - Additional CSS classes applied to the item element.
 * @param children - The display text for this option.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Item`, including `value` and `disabled`.
 * @returns A selectable item row with text and optional check indicator.
 *
 * @example
 * ```tsx
 * <SelectContent>
 *   <SelectItem value="light">Light</SelectItem>
 *   <SelectItem value="dark" disabled>Dark (unavailable)</SelectItem>
 * </SelectContent>
 * ```
 */
function SelectItem({
  className,
  children,
  ...props
}: SelectPrimitive.Item.Props) {
  return (
    <SelectPrimitive.Item
      data-slot="select-item"
      className={cn(
        "relative flex w-full cursor-default items-center gap-1.5 rounded-md py-1 pr-8 pl-1.5 text-sm outline-hidden select-none focus:bg-accent focus:text-accent-foreground not-data-[variant=destructive]:focus:**:text-accent-foreground data-disabled:pointer-events-none data-disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4 *:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2",
        className
      )}
      {...props}
    >
      <SelectPrimitive.ItemText className="flex flex-1 shrink-0 gap-2 whitespace-nowrap">
        {children}
      </SelectPrimitive.ItemText>
      <SelectPrimitive.ItemIndicator
        render={
          <span className="pointer-events-none absolute right-2 flex size-4 items-center justify-center" />
        }
      >
        <CheckIcon className="pointer-events-none" />
      </SelectPrimitive.ItemIndicator>
    </SelectPrimitive.Item>
  )
}

/**
 * A visual separator line between groups or sections of items.
 *
 * Renders a `<div>` element with `data-slot="select-separator"`.
 * Draws a horizontal rule with standard border styling.
 *
 * @param className - Additional CSS classes applied to the separator element.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.Separator`.
 * @returns A horizontal divider line within the select popup.
 *
 * @example
 * ```tsx
 * <SelectContent>
 *   <SelectItem value="a">Option A</SelectItem>
 *   <SelectSeparator />
 *   <SelectItem value="b">Option B</SelectItem>
 * </SelectContent>
 * ```
 */
function SelectSeparator({
  className,
  ...props
}: SelectPrimitive.Separator.Props) {
  return (
    <SelectPrimitive.Separator
      data-slot="select-separator"
      className={cn("pointer-events-none -mx-1 my-1 h-px bg-border", className)}
      {...props}
    />
  )
}

/**
 * A scroll button that appears at the top of the select popup.
 *
 * Renders a `<div>` with an up-arrow chevron icon. Visible only when
 * the list content overflows above the viewport. Hovering scrolls the
 * list upward. Does not render on touch devices.
 *
 * @param className - Additional CSS classes applied to the scroll button element.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.ScrollUpArrow`.
 * @returns A scroll-up button that appears when content overflows upward.
 */
function SelectScrollUpButton({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollUpArrow>) {
  return (
    <SelectPrimitive.ScrollUpArrow
      data-slot="select-scroll-up-button"
      className={cn(
        "top-0 z-10 flex w-full cursor-default items-center justify-center bg-popover py-1 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      <ChevronUpIcon
      />
    </SelectPrimitive.ScrollUpArrow>
  )
}

/**
 * A scroll button that appears at the bottom of the select popup.
 *
 * Renders a `<div>` with a down-arrow chevron icon. Visible only when
 * the list content overflows below the viewport. Hovering scrolls the
 * list downward. Does not render on touch devices.
 *
 * @param className - Additional CSS classes applied to the scroll button element.
 * @param props - Additional props forwarded to the underlying `SelectPrimitive.ScrollDownArrow`.
 * @returns A scroll-down button that appears when content overflows downward.
 */
function SelectScrollDownButton({
  className,
  ...props
}: React.ComponentProps<typeof SelectPrimitive.ScrollDownArrow>) {
  return (
    <SelectPrimitive.ScrollDownArrow
      data-slot="select-scroll-down-button"
      className={cn(
        "bottom-0 z-10 flex w-full cursor-default items-center justify-center bg-popover py-1 [&_svg:not([class*='size-'])]:size-4",
        className
      )}
      {...props}
    >
      <ChevronDownIcon
      />
    </SelectPrimitive.ScrollDownArrow>
  )
}

export {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectScrollDownButton,
  SelectScrollUpButton,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
}
