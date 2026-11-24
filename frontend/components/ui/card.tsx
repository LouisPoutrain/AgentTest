import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * A container component that groups related content into a visually distinct card.
 * Supports two sizes: "default" and "sm". Use child components (CardHeader, CardTitle,
 * CardDescription, CardContent, CardFooter, CardAction) to structure the interior.
 *
 * @example
 * ```tsx
 * <Card>
 *   <CardHeader>
 *     <CardTitle>Project Status</CardTitle>
 *     <CardDescription>Current deployment information</CardDescription>
 *   </CardHeader>
 *   <CardContent>
 *     <p>All systems operational</p>
 *   </CardContent>
 *   <CardFooter>
 *     <Button>View Details</Button>
 *   </CardFooter>
 * </Card>
 * ```
 */
function Card({
  className,
  size = "default",
  ...props
}: React.ComponentProps<"div"> & { size?: "default" | "sm" }) {
  return (
    <div
      data-slot="card"
      data-size={size}
      className={cn(
        "group/card flex flex-col gap-(--card-spacing) overflow-hidden rounded-xl bg-bg-elevated py-(--card-spacing) text-sm text-card-foreground ring-1 ring-border shadow-sm [--card-spacing:--spacing(4)] has-data-[slot=card-footer]:pb-0 has-[>img:first-child]:pt-0 data-[size=sm]:[--card-spacing:--spacing(3)] data-[size=sm]:has-data-[slot=card-footer]:pb-0 *:[img:first-child]:rounded-t-xl *:[img:last-child]:rounded-b-xl",
        className
      )}
      {...props}
    />
  )
}

/**
 * The header section of a card. Typically contains the title and description.
 * Renders with top rounded corners and a bottom border when used with a bordered card.
 *
 * @example
 * ```tsx
 * <CardHeader>
 *   <CardTitle>My Title</CardTitle>
 *   <CardDescription>Optional description text</CardDescription>
 * </CardHeader>
 * ```
 */
function CardHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "group/card-header @container/card-header grid auto-rows-min items-start gap-1 rounded-t-xl px-(--card-spacing) has-data-[slot=card-action]:grid-cols-[1fr_auto] has-data-[slot=card-description]:grid-rows-[auto_auto] [.border-b]:pb-(--card-spacing)",
        className
      )}
      {...props}
    />
  )
}

/**
 * The title text displayed in a card header. Uses a heading font style with
 * semibold weight and base size, scaling down to small in compact cards.
 */
function CardTitle({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-title"
      className={cn(
        "font-heading text-base leading-snug font-semibold group-data-[size=sm]/card:text-sm",
        className
      )}
      {...props}
    />
  )
}

/**
 * A secondary description text displayed beneath the card title.
 * Renders in a muted text color at small size.
 */
function CardDescription({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-description"
      className={cn("text-sm text-text-secondary", className)}
      {...props}
    />
  )
}

/**
 * An action element (such as a button or icon) positioned in the top-right corner
 * of the card header. Used alongside CardTitle for secondary actions like menus,
 * settings, or quick actions.
 *
 * @example
 * ```tsx
 * <CardHeader>
 *   <CardTitle>Messages</CardTitle>
 *   <CardAction>
 *     <Button variant="ghost" size="icon">
 *       <MoreHorizontalIcon />
 *     </Button>
 *   </CardAction>
 * </CardHeader>
 * ```
 */
function CardAction({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-action"
      className={cn(
        "col-start-2 row-span-2 row-start-1 self-start justify-self-end",
        className
      )}
      {...props}
    />
  )
}

/**
 * The main content area of a card. Renders with horizontal padding aligned to
 * the card's spacing variable. Place primary content, forms, or data visualizations here.
 */
function CardContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-content"
      className={cn("px-(--card-spacing)", className)}
      {...props}
    />
  )
}

/**
 * A footer section for a card, rendered with a top border, subtle background,
 * and rounded bottom corners. Typically used for action buttons, metadata, or
 * supplementary information that should be visually separated from the main content.
 *
 * @example
 * ```tsx
 * <CardFooter>
 *   <Button variant="outline">Cancel</Button>
 *   <Button>Confirm</Button>
 * </CardFooter>
 * ```
 */
function CardFooter({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex items-center rounded-b-xl border-t bg-bg-secondary/50 p-(--card-spacing)",
        className
      )}
      {...props}
    />
  )
}

export {
  Card,
  CardHeader,
  CardFooter,
  CardTitle,
  CardAction,
  CardDescription,
  CardContent,
}
