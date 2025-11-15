import type { CartItem } from '@/features/cart/types';

export interface CheckoutFormData {
  fullName: string;
  email: string;
  address: string;
  phone: string;
  cardNumber: string;
  expiry: string;
  cvv: string;
}

export interface CheckoutState {
  items: CartItem[];
  isAnalyzing: boolean;
  analysisComplete: boolean;
  error: string | null;
}
