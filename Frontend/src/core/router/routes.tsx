import { createBrowserRouter } from 'react-router-dom';
import { BookingsPage } from '@/features/bookings';
import { CheckoutPage } from '@/features/checkout';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <BookingsPage />,
  },
  {
    path: '/booking',
    element: <BookingsPage />,
  },
  {
    path: '/checkout',
    element: <CheckoutPage />,
  },
  // Add more routes here as features are developed
  // {
  //   path: '/tracking/:orderId',
  //   element: <OrderTrackingPage />,
  // },
]);
