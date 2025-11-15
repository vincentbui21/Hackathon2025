import { useCartStore } from '../store';

export function useCart() {
  const {
    items,
    totalItems,
    totalPrice,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    getItemQuantity,
    updateWarnings,
    getWarningCount,
  } = useCartStore();

  return {
    items,
    totalItems,
    totalPrice,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    getItemQuantity,
    updateWarnings,
    warningCount: getWarningCount(),
  };
}
