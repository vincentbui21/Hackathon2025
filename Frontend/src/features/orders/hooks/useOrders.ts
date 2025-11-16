import { useQuery } from '@tanstack/react-query';
import { ordersService } from '../services';
import type { Order } from '../types';

export const orderKeys = {
  all: ['orders'] as const,
  lists: () => [...orderKeys.all, 'list'] as const,
  list: (filters?: any) => [...orderKeys.lists(), filters] as const,
  details: () => [...orderKeys.all, 'detail'] as const,
  detail: (id: string) => [...orderKeys.details(), id] as const,
};

export function useOrders() {
  return useQuery<Order[], Error>({
    queryKey: orderKeys.lists(),
    queryFn: () => ordersService.getOrders(),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useOrder(id: string) {
  return useQuery<Order, Error>({
    queryKey: orderKeys.detail(id),
    queryFn: () => ordersService.getOrderById(id),
    enabled: !!id,
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
