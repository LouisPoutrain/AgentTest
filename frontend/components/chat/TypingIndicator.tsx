export function TypingIndicator() {
  return (
    <div className="flex items-center gap-1.5 px-4 py-3 bg-bg-secondary/30 rounded-lg w-fit ml-12">
      <div className="w-2 h-2 rounded-full bg-text-secondary/50 animate-bounce" style={{ animationDelay: "0ms" }} />
      <div className="w-2 h-2 rounded-full bg-text-secondary/50 animate-bounce" style={{ animationDelay: "150ms" }} />
      <div className="w-2 h-2 rounded-full bg-text-secondary/50 animate-bounce" style={{ animationDelay: "300ms" }} />
    </div>
  );
}
