import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { Order, OrdersResponse } from '../types';

class OrdersService {
  async getOrders(): Promise<Order[]> {
    const response = await apiClient.get<OrdersResponse>(API_ENDPOINTS.BOOKING_ORDERS);
    return response.orders;
  }

  async getOrderById(id: string): Promise<Order> {
    return apiClient.get<Order>(API_ENDPOINTS.ORDER_BY_ID(id));
  }

  async createOrder(orderData: Partial<Order>): Promise<Order> {
    return apiClient.post<Order>(API_ENDPOINTS.ORDER, orderData);
  }

  async trackOrder(orderNumber: string): Promise<any> {
    return apiClient.get(API_ENDPOINTS.ORDER_TRACKING(orderNumber));
  }

  async validateOrder(orderId: number, imageFile: File): Promise<any> {
    const formData = new FormData();
    formData.append('order_id', orderId.toString());
    formData.append('image', imageFile);

    // Use fetch directly to avoid JSON.stringify on FormData
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';
    const url = `${API_BASE_URL}${API_ENDPOINTS.VALIDATE_ORDER}`;

    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type header - browser will set it automatically with boundary
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Upload failed: ${response.status} - ${errorText}`);
    }

    return response.json();
  }
}

export const ordersService = new OrdersService();
