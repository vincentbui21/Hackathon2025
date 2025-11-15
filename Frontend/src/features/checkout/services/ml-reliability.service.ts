import { apiClient } from '@/core/api';
import type { MLPredictionRequest, MLPredictionResponse } from '../types';

const USE_MOCK_DATA = true; // Toggle when backend is ready

class MLReliabilityService {
  async predictReliability(productIds: number[]): Promise<MLPredictionResponse> {
    if (USE_MOCK_DATA) {
      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 1500));

      // Mock predictions with varying scores for demonstration
      const predictions = productIds.map((id) => ({
        product_id: id,
        // Generate varied scores for testing:
        // 101: 0.35 (critical), 102: 0.55 (warning), 103: 0.85 (info/good)
        score: id === 101 ? 0.35 : id === 102 ? 0.55 : id === 103 ? 0.25 : Math.random() * 0.4 + 0.4,
      }));

      return { predictions };
    }

    const requestBody: MLPredictionRequest = {
      product_ids: productIds,
    };

    return apiClient.post<MLPredictionResponse>('/checkout/predict', requestBody);
  }
}

export const mlReliabilityService = new MLReliabilityService();
