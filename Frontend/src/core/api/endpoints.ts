export const API_ENDPOINTS = {
  // Bookings/Products
  PRODUCTS: '/booking/products',
  PRODUCT_BY_ID: (id: string) => `/booking/products/${id}`,

  // Checkout
  RELIABILITY_CHECK: '/reliability/check',
  SUBSTITUTES: '/service/alternative',

  // Orders
  ORDER: '/checkout/order',
  ORDERS: '/checkout/order',
  BOOKING_ORDERS: '/booking/orders',
  ORDER_BY_ID: (id: string) => `/orders/${id}`,
  ORDER_TRACKING: (orderNumber: string) => `/orders/${orderNumber}/tracking`,
  VALIDATE_ORDER: '/validate',

  // Chat
  CHAT_MESSAGE: '/chat/message',
  CHAT_CLEAR: '/chat/clear',
  CHAT_ORDER_APOLOGY: '/chat/order-apology',
} as const;
