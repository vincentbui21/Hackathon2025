import { Alert, AlertDescription } from '@/shared/components/ui/alert';
import { Badge } from '@/shared/components/ui/badge';
import { AlertTriangle, XCircle, Info } from 'lucide-react';
import type { ProductWarning } from '../types';
import { warningBuilderService } from '../services';

interface ProductWarningCardProps {
  warning: ProductWarning;
  productName: string;
}

export function ProductWarningCard({ warning, productName }: ProductWarningCardProps) {
  const colors = warningBuilderService.getWarningColor(warning.severity);

  const Icon =
    warning.severity === 'critical'
      ? XCircle
      : warning.severity === 'warning'
      ? AlertTriangle
      : Info;

  const badgeVariant =
    warning.severity === 'critical'
      ? 'destructive'
      : warning.severity === 'warning'
      ? 'default'
      : 'secondary';

  return (
    <Alert className={`${colors.bg} ${colors.border} border`}>
      <div className="flex gap-3">
        <div className="flex-shrink-0 mt-0.5">
          <Icon className={`w-5 h-5 ${colors.text}`} />
        </div>
        <div className="flex-1 space-y-2">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-sm">{productName}</p>
            <Badge variant={badgeVariant} className="text-xs">
              {warning.severity.toUpperCase()}
            </Badge>
          </div>
          <AlertDescription className={`${colors.text} space-y-1`}>
            <p className="font-medium">{warning.message}</p>
            {warning.details && (
              <p className="text-sm opacity-90">{warning.details}</p>
            )}
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}
