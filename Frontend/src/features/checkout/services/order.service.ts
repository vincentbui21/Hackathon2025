import { apiClient, API_ENDPOINTS } from '@/core/api';

export interface TrackingItem {
  product_id: number;
  ordered_quantity: number;
}

export interface OrderPayload {
  total: number;
  tracking: TrackingItem[];
}

export interface OrderResponse {
  success: boolean;
  order_id?: string;
  message?: string;
}

class OrderService {
  async createOrder(total: number, tracking: TrackingItem[]): Promise<OrderResponse> {
    const payload: OrderPayload = { total, tracking };
    return apiClient.post<OrderResponse>(API_ENDPOINTS.ORDER, payload);
  }
}

export const orderService = new OrderService();
