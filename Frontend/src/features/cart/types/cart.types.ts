import type { Product } from '@/features/bookings/types';
import type { ProductWarning } from '@/features/checkout/types';

export interface CartItem extends Product {
  quantity: number;
  warning?: ProductWarning | null;
}

export interface CartState {
  items: CartItem[];
  totalItems: number;
  totalPrice: number;
}
