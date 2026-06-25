import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
      <Icon className="h-10 w-10 text-muted-foreground/50" />
      <p className="font-medium">{title}</p>
      <p className="text-sm text-muted-foreground max-w-xs">{description}</p>
      {action}
    </div>
  );
}
