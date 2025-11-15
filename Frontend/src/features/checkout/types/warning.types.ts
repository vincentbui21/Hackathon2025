export type WarningSeverity = 'critical' | 'warning' | 'info';

export interface ProductWarning {
  productId: number;
  severity: WarningSeverity;
  score: number; // 0-1, where lower is worse
  message: string;
  details?: string;
}

export interface MLPrediction {
  product_id: number;
  score: number;
}

export interface MLPredictionResponse {
  predictions: MLPrediction[];
}

export interface MLPredictionRequest {
  product_ids: number[];
}
