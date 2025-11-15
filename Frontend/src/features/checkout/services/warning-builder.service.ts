import type { MLPrediction, ProductWarning, WarningSeverity } from '../types';

// Thresholds for determining severity based on ML score
const CRITICAL_THRESHOLD = 0.4; // score < 0.4 = critical
const WARNING_THRESHOLD = 0.7;  // score < 0.7 = warning
// score >= 0.7 = info/good (no warning needed)

class WarningBuilderService {
  buildWarningFromPrediction(prediction: MLPrediction): ProductWarning | null {
    const { product_id, score } = prediction;

    // Don't create warning if score is good
    if (score >= WARNING_THRESHOLD) {
      return null;
    }

    const severity = this.determineSeverity(score);
    const { message, details } = this.generateWarningMessage(score, severity);

    return {
      productId: product_id,
      severity,
      score,
      message,
      details,
    };
  }

  buildWarningsFromPredictions(predictions: MLPrediction[]): ProductWarning[] {
    return predictions
      .map((prediction) => this.buildWarningFromPrediction(prediction))
      .filter((warning): warning is ProductWarning => warning !== null);
  }

  private determineSeverity(score: number): WarningSeverity {
    if (score < CRITICAL_THRESHOLD) {
      return 'critical';
    } else if (score < WARNING_THRESHOLD) {
      return 'warning';
    }
    return 'info';
  }

  private generateWarningMessage(
    score: number,
    severity: WarningSeverity
  ): { message: string; details: string } {
    const percentage = Math.round(score * 100);

    if (severity === 'critical') {
      return {
        message: `High Risk - Reliability Score: ${percentage}%`,
        details:
          'This product has a history of delivery delays, stock shortages, or quality issues. Consider selecting an alternative product.',
      };
    } else if (severity === 'warning') {
      return {
        message: `Moderate Risk - Reliability Score: ${percentage}%`,
        details:
          'This product may experience occasional delays or availability issues. We recommend reviewing alternatives or adjusting your order timeline.',
      };
    }

    return {
      message: `Low Risk - Reliability Score: ${percentage}%`,
      details: 'This product has a good track record.',
    };
  }

  getWarningColor(severity: WarningSeverity): {
    bg: string;
    border: string;
    text: string;
  } {
    switch (severity) {
      case 'critical':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-800',
        };
      case 'warning':
        return {
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          text: 'text-amber-800',
        };
      case 'info':
        return {
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          text: 'text-blue-800',
        };
    }
  }
}

export const warningBuilderService = new WarningBuilderService();
