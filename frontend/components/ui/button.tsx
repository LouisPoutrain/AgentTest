import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

/**
 * Defines the visual variants and sizes for the Button component using
 * class-variance-authority (CVA). Each variant maps to a set of Tailwind CSS
 * utility classes that control appearance, hover states, and accessibility.
 *
 * @example
 * // Default button
 * buttonVariants({ variant: "default", size: "default" })
 *
 * // Destructive action button
 * buttonVariants({ variant: "destructive", size: "sm" })
 *
 * // Icon-only button
 * buttonVariants({ variant: "ghost", size: "icon" })
 */
const buttonVariants = cva(
  "group/button inline-flex shrink-0 items-center justify-center rounded-lg border border-transparent bg-clip-padding text-sm font-medium whitespace-nowrap transition-all duration-200 ease-out outline-none select-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 active:not-aria-[haspopup]:translate-y-px disabled:pointer-events-none disabled:opacity-50 aria-invalid:border-destructive aria-invalid:ring-3 aria-invalid:ring-destructive/20 dark:aria-invalid:border-destructive/50 dark:aria-invalid:ring-destructive/40 [&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/80 shadow-sm hover:shadow-md",
        outline:
          "border-border bg-background hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:border-input dark:bg-input/30 dark:hover:bg-input/50",
        secondary:
          "bg-bg-secondary text-text-primary border-border hover:bg-bg-tertiary hover:text-text-primary",
        ghost:
          "hover:bg-muted hover:text-foreground aria-expanded:bg-muted aria-expanded:text-foreground dark:hover:bg-muted/50",
        destructive:
          "bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-900/50",
        link: "text-primary underline-offset-4 hover:underline",
        // Warm & Cozy custom variants
        "agent-primary": "bg-accent hover:bg-accent-hover text-white shadow-sm hover:shadow-md",
        "agent-secondary": "bg-bg-secondary text-text-primary border-border hover:bg-bg-tertiary",
      },
      size: {
        default: "h-8 gap-1.5 px-2.5 has-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        xs: "h-6 gap-1 rounded-[min(var(--radius-md),10px)] px-2 text-xs in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3",
        sm: "h-7 gap-1 rounded-[min(var(--radius-md),12px)] px-2.5 text-[0.8rem] in-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5 [&_svg:not([class*='size-'])]:size-3.5",
        lg: "h-9 gap-1.5 px-2.5 has-data-[slot=button-group]:rounded-lg has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2",
        icon: "size-8",
        "icon-xs": "size-6 rounded-[min(var(--radius-md),10px)] in-data-[slot=button-group]:rounded-lg [&_svg:not([class*='size-'])]:size-3",
        "icon-sm": "size-7 rounded-[min(var(--radius-md),12px)] in-data-[slot=button-group]:rounded-lg",
        "icon-lg": "size-9",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

/**
 * Props for the Button component. Extends standard HTML button attributes
 * with CVA variant/size props and an optional asChild prop for composition
 * with Radix UI Slot.
 */
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  /** When true, renders the button as its child component instead of a native `<button>` element. Useful for composing with Next.js Link or Radix UI primitives. */
  asChild?: boolean;
}

/**
 * A versatile, accessible button component built with Radix UI Slot and
 * class-variance-authority for variant/size theming.
 *
 * Supports all standard HTML button attributes plus CVA-based visual variants
 * and sizes. Use `asChild` to compose with Next.js Link or other Radix UI
 * components without adding an extra DOM node.
 *
 * @example
 * // Basic usage
 * <Button onClick={handleClick}>Click me</Button>
 *
 * // Destructive action with custom size
 * <Button variant="destructive" size="sm">Delete</Button>
 *
 * // Composed with Next.js Link (asChild)
 * <Link href="/dashboard">
 *   <Button asChild>Dashboard</Button>
 * </Link>
 *
 * @example
 * // Icon-only button
 * <Button variant="ghost" size="icon" aria-label="Settings">
 *   <SettingsIcon />
 * </Button>
 *
 * @template T - The HTML element type (defaults to HTMLButtonElement)
 */
const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

/**
 * The Button component — a styled, accessible button supporting variants,
 * sizes, and composition via Radix UI Slot.
 *
 * @example
 * <Button variant="default" size="default">Submit</Button>
 *
 * @returns A `<button>` element (or child component when `asChild` is true)
 * with applied variant/size classes and standard button semantics.
 */
export { Button, buttonVariants };
