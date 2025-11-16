import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { Product } from '../types';

interface ProductsResponse {
  products: Product[];
}

class BookingsService {
  async getAllProducts(): Promise<Product[]> {
    const response = await apiClient.get<ProductsResponse>(API_ENDPOINTS.PRODUCTS);
    return response.products;
  }

  async getProductById(id: number): Promise<Product | null> {
    return apiClient.get<Product>(API_ENDPOINTS.PRODUCT_BY_ID(id.toString()));
  }

  async searchProducts(query: string): Promise<Product[]> {
    const response = await apiClient.get<ProductsResponse>(`${API_ENDPOINTS.PRODUCTS}?search=${query}`);
    return response.products;
  }
}

export const bookingsService = new BookingsService();
