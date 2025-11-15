import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type { Product } from '@/features/bookings/types';
import type { CartItem } from '../types';

interface CartStore {
  items: CartItem[];

  // Computed values
  totalItems: number;
  totalPrice: number;

  // Actions
  addItem: (product: Product) => void;
  removeItem: (productId: number) => void;
  updateQuantity: (productId: number, quantity: number) => void;
  clearCart: () => void;
  getItemQuantity: (productId: number) => number;
  updateWarnings: (warnings: Map<number, any>) => void;
  getWarningCount: () => number;
}

const calculateTotals = (items: CartItem[]) => {
  const totalItems = items.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = items.reduce((sum, item) => sum + item.Price * item.quantity, 0);
  return { totalItems, totalPrice };
};

export const useCartStore = create<CartStore>()(
  devtools(
    persist(
      (set, get) => ({
        items: [],
        totalItems: 0,
        totalPrice: 0,

        addItem: (product) => {
          set((state) => {
            const existingItem = state.items.find((item) => item.ProductID === product.ProductID);

            let newItems: CartItem[];
            if (existingItem) {
              // Increment quantity if item already in cart
              newItems = state.items.map((item) =>
                item.ProductID === product.ProductID
                  ? { ...item, quantity: item.quantity + 1 }
                  : item
              );
            } else {
              // Add new item to cart
              newItems = [...state.items, { ...product, quantity: 1 }];
            }

            return {
              items: newItems,
              ...calculateTotals(newItems),
            };
          });
        },

        removeItem: (productId) => {
          set((state) => {
            const newItems = state.items.filter((item) => item.ProductID !== productId);
            return {
              items: newItems,
              ...calculateTotals(newItems),
            };
          });
        },

        updateQuantity: (productId, quantity) => {
          if (quantity <= 0) {
            get().removeItem(productId);
            return;
          }

          set((state) => {
            const newItems = state.items.map((item) =>
              item.ProductID === productId ? { ...item, quantity } : item
            );
            return {
              items: newItems,
              ...calculateTotals(newItems),
            };
          });
        },

        clearCart: () => {
          set({ items: [], totalItems: 0, totalPrice: 0 });
        },

        getItemQuantity: (productId) => {
          const item = get().items.find((item) => item.ProductID === productId);
          return item?.quantity || 0;
        },

        updateWarnings: (warnings) => {
          set((state) => {
            const newItems = state.items.map((item) => ({
              ...item,
              warning: warnings.get(item.ProductID) || null,
            }));
            return {
              items: newItems,
              ...calculateTotals(newItems),
            };
          });
        },

        getWarningCount: () => {
          return get().items.filter((item) => item.warning !== null && item.warning !== undefined).length;
        },
      }),
      {
        name: 'cart-storage',
      }
    ),
    { name: 'cart-store' }
  )
);
