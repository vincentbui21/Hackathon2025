import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { Product } from '@/features/bookings/types';

interface SubstitutionResponse {
  product: Product;
  alternatives: Product[];
}

class SubstitutionService {
  async getSubstitutes(productId: number): Promise<Product[]> {
    const response = await apiClient.post<SubstitutionResponse>(
      API_ENDPOINTS.SUBSTITUTES,
      { product_id: productId }
    );

    console.log('Substitution response:', response);

    // Return alternatives with prediction scores
    const alternatives = response.alternatives || [];

    // Sort by prediction score (highest first)
    return alternatives.sort((a, b) => {
      const scoreA = a.Prediction_score ?? 0;
      const scoreB = b.Prediction_score ?? 0;
      return scoreB - scoreA;
    });
  }
}

export const substitutionService = new SubstitutionService();
