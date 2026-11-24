"use client"

import * as React from "react"
import { Dialog as DialogPrimitive } from "@base-ui/react/dialog"

import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { XIcon } from "lucide-react"

/**
 * Root Dialog component that manages open/close state and provides context
 * for nested dialog parts.
 *
 * @param props - Props from `@base-ui/react/dialog` Root component.
 * @returns The root dialog element with state management.
 *
 * @example
 * ```tsx
 * <Dialog open={isOpen} onOpenChange={setIsOpen}>
 *   <DialogTrigger>Open</DialogTrigger>
 *   <DialogContent>
 *     <DialogTitle>Title</DialogTitle>
 *     <DialogDescription>Description</DialogDescription>
 *     <DialogFooter>
 *       <Button onClick={() => setIsOpen(false)}>Close</Button>
 *     </DialogFooter>
 *   </DialogContent>
 * </Dialog>
 * ```
 */
function Dialog({ ...props }: DialogPrimitive.Root.Props) {
  return <DialogPrimitive.Root data-slot="dialog" {...props} />
}

/**
 * Button or element that opens the dialog when clicked or activated.
 *
 * @param props - Props from `@base-ui/react/dialog` Trigger component.
 * @returns The trigger element that controls dialog opening.
 *
 * @example
 * ```tsx
 * <DialogTrigger asChild>
 *   <Button variant="outline">Open Dialog</Button>
 * </DialogTrigger>
 * ```
 */
function DialogTrigger({ ...props }: DialogPrimitive.Trigger.Props) {
  return <DialogPrimitive.Trigger data-slot="dialog-trigger" {...props} />
}

/**
 * Portals the dialog content to the document body, ensuring proper z-index
 * and focus management outside the normal DOM hierarchy.
 *
 * @param props - Props from `@base-ui/react/dialog` Portal component.
 * @returns The portal container for the dialog overlay and content.
 *
 * @example
 * ```tsx
 * <DialogPortal>
 *   <DialogOverlay />
 *   <DialogContent>...</DialogContent>
 * </DialogPortal>
 * ```
 */
function DialogPortal({ ...props }: DialogPrimitive.Portal.Props) {
  return <DialogPrimitive.Portal data-slot="dialog-portal" {...props} />
}

/**
 * Button or element that closes the dialog when activated.
 *
 * @param props - Props from `@base-ui/react/dialog` Close component.
 * @returns The close button element that dismisses the dialog.
 *
 * @example
 * ```tsx
 * <DialogClose asChild>
 *   <Button variant="ghost">Cancel</Button>
 * </DialogClose>
 * ```
 */
function DialogClose({ ...props }: DialogPrimitive.Close.Props) {
  return <DialogPrimitive.Close data-slot="dialog-close" {...props} />
}

/**
 * Semi-transparent backdrop that covers the viewport behind the dialog.
 * Clicking the overlay closes the dialog.
 *
 * @param className - Additional CSS classes applied to the overlay element.
 * @param props - Props from `@base-ui/react/dialog` Backdrop component.
 * @returns The backdrop overlay element with fade animation.
 */
function DialogOverlay({
  className,
  ...props
}: DialogPrimitive.Backdrop.Props) {
  return (
    <DialogPrimitive.Backdrop
      data-slot="dialog-overlay"
      className={cn(
        "fixed inset-0 isolate z-50 bg-black/10 duration-100 supports-backdrop-filter:backdrop-blur-xs data-open:animate-in data-open:fade-in-0 data-closed:animate-out data-closed:fade-out-0",
        className
      )}
      {...props}
    />
  )
}

/**
 * Main dialog content panel, centered on screen with overlay backdrop.
 * Includes a close button in the top-right corner by default.
 *
 * @param className - Additional CSS classes applied to the popup container.
 * @param children - Dialog body content (title, description, form elements, etc.).
 * @param showCloseButton - Whether to render the close button in the top-right corner.
 *   Defaults to `true`. Set to `false` when managing close behavior externally.
 * @param props - Props from `@base-ui/react/dialog` Popup component plus custom props.
 * @returns The centered dialog popup with overlay, close button, and fade/zoom animations.
 *
 * @example
 * ```tsx
 * <DialogContent>
 *   <DialogHeader>
 *     <DialogTitle>Delete item</DialogTitle>
 *     <DialogDescription>
 *       This action cannot be undone.
 *     </DialogDescription>
 *   </DialogHeader>
 *   <DialogFooter showCloseButton>
 *     <Button variant="destructive">Delete</Button>
 *   </DialogFooter>
 * </DialogContent>
 * ```
 */
function DialogContent({
  className,
  children,
  showCloseButton = true,
  ...props
}: DialogPrimitive.Popup.Props & {
  showCloseButton?: boolean
}) {
  return (
    <DialogPortal>
      <DialogOverlay />
      <DialogPrimitive.Popup
        data-slot="dialog-content"
        className={cn(
          "fixed top-1/2 left-1/2 z-50 grid w-full max-w-[calc(100%-2rem)] -translate-x-1/2 -translate-y-1/2 gap-4 rounded-xl bg-popover p-4 text-sm text-popover-foreground ring-1 ring-foreground/10 duration-100 outline-none sm:max-w-sm data-open:animate-in data-open:fade-in-0 data-open:zoom-in-95 data-closed:animate-out data-closed:fade-out-0 data-closed:zoom-out-95",
          className
        )}
        {...props}
      >
        {children}
        {showCloseButton && (
          <DialogPrimitive.Close
            data-slot="dialog-close"
            render={
              <Button
                variant="ghost"
                className="absolute top-2 right-2"
                size="icon-sm"
              />
            }
          >
            <XIcon
            />
            <span className="sr-only">Close</span>
          </DialogPrimitive.Close>
        )}
      </DialogPrimitive.Popup>
    </DialogPortal>
  )
}

/**
 * Header section for the dialog, stacking title and description vertically.
 *
 * @param className - Additional CSS classes applied to the header container.
 * @param props - Standard HTML div props passed through to the element.
 * @returns A flex container for dialog header content.
 *
 * @example
 * ```tsx
 * <DialogHeader>
 *   <DialogTitle>My Title</DialogTitle>
 *   <DialogDescription>Optional description text.</DialogDescription>
 * </DialogHeader>
 * ```
 */
function DialogHeader({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="dialog-header"
      className={cn("flex flex-col gap-2", className)}
      {...props}
    />
  )
}

/**
 * Footer section for the dialog, containing action buttons and an optional
 * default close button. Sticks to the bottom with inverted margins to match
 * the dialog border radius.
 *
 * @param className - Additional CSS classes applied to the footer container.
 * @param showCloseButton - Whether to render a default "Close" button on the right.
 *   Defaults to `false`. When `true`, renders a ghost-style close button.
 * @param children - Action buttons or other content to display in the footer.
 * @param props - Standard HTML div props passed through to the element.
 * @returns A styled footer container with optional close button and reversed layout.
 *
 * @example
 * ```tsx
 * <DialogFooter>
 *   <Button variant="secondary">Cancel</Button>
 *   <Button variant="default">Confirm</Button>
 * </DialogFooter>
 *
 * // With default close button
 * <DialogFooter showCloseButton>
 *   <Button variant="default">Save</Button>
 * </DialogFooter>
 * ```
 */
function DialogFooter({
  className,
  showCloseButton = false,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  showCloseButton?: boolean
}) {
  return (
    <div
      data-slot="dialog-footer"
      className={cn(
        "-mx-4 -mb-4 flex flex-col-reverse gap-2 rounded-b-xl border-t bg-muted/50 p-4 sm:flex-row sm:justify-end",
        className
      )}
      {...props}
    >
      {children}
      {showCloseButton && (
        <DialogPrimitive.Close render={<Button variant="outline" />}>
          Close
        </DialogPrimitive.Close>
      )}
    </div>
  )
}

/**
 * Primary heading for the dialog, rendered as an `<h4>` element.
 * Provides heading semantics and visual styling for the dialog title.
 *
 * @param className - Additional CSS classes applied to the title element.
 * @param props - Props from `@base-ui/react/dialog` Title component.
 * @returns The dialog title heading element.
 *
 * @example
 * ```tsx
 * <DialogHeader>
 *   <DialogTitle>Edit Profile</DialogTitle>
 * </DialogHeader>
 * ```
 */
function DialogTitle({ className, ...props }: DialogPrimitive.Title.Props) {
  return (
    <DialogPrimitive.Title
      data-slot="dialog-title"
      className={cn(
        "font-heading text-base leading-none font-medium",
        className
      )}
      {...props}
    />
  )
}

/**
 * Descriptive text for the dialog, providing context or instructions below the title.
 * Rendered as a `<div>` with muted text styling and link formatting.
 *
 * @param className - Additional CSS classes applied to the description element.
 * @param props - Props from `@base-ui/react/dialog` Description component.
 * @returns The dialog description element with muted text styling.
 *
 * @example
 * ```tsx
 * <DialogDescription>
 *   Changes will be applied immediately. Make sure you have selected the correct item.
 * </DialogDescription>
 * ```
 */
function DialogDescription({
  className,
  ...props
}: DialogPrimitive.Description.Props) {
  return (
    <DialogPrimitive.Description
      data-slot="dialog-description"
      className={cn(
        "text-sm text-muted-foreground *:[a]:underline *:[a]:underline-offset-3 *:[a]:hover:text-foreground",
        className
      )}
      {...props}
    />
  )
}

export {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogOverlay,
  DialogPortal,
  DialogTitle,
  DialogTrigger,
}
