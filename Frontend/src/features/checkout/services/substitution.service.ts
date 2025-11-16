import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { Product } from '@/features/bookings/types';

interface SubstitutionResponse {
  alternatives: Product[];
}

class SubstitutionService {
  async getSubstitutes(productId: number): Promise<Product[]> {
    const response = await apiClient.post<SubstitutionResponse>(
      API_ENDPOINTS.SUBSTITUTES,
      { product_id: productId }
    );

    console.log('Substitution response:', response);
    return response.alternatives;
  }
}

export const substitutionService = new SubstitutionService();
