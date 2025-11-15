export const API_ENDPOINTS = {
  // Bookings/Products
  PRODUCTS: '/products',
  PRODUCT_BY_ID: (id: string) => `/products/${id}`,

  // Checkout
  RELIABILITY_CHECK: '/reliability/check',
  SUBSTITUTES: (productId: string) => `/products/${productId}/substitutes`,

  // Orders
  ORDERS: '/orders',
  ORDER_BY_ID: (id: string) => `/orders/${id}`,
  ORDER_TRACKING: (orderNumber: string) => `/orders/${orderNumber}/tracking`,
} as const;
