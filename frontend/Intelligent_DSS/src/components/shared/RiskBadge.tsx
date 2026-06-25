import { Badge } from "@/components/ui/badge";
import { RISK_COLORS } from "@/lib/constants";
import type { RiskClass } from "@/types/prediction.types";

interface Props {
  risk: RiskClass;
}

export function RiskBadge({ risk }: Props) {
  return (
    <Badge className={RISK_COLORS[risk]} variant="outline">
      {risk} Risk
    </Badge>
  );
}
