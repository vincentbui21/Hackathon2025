import { createBrowserRouter } from 'react-router-dom';
import { BookingsPage } from '@/features/bookings';
import { CheckoutPage } from '@/features/checkout';
import { OrdersPage } from '@/features/orders';
import { DashboardPage } from '@/features/dashboard';
import { ChatPage } from '@/features/chat';
import { DashboardLayout } from '@/shared/components/layout';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <DashboardLayout />,
    children: [
      {
        index: true,
        element: <DashboardPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'booking',
        element: <BookingsPage />,
      },
      {
        path: 'checkout',
        element: <CheckoutPage />,
      },
      {
        path: '/order',
        element: <OrdersPage />,
      },
      {
        path: 'chat',
        element: <ChatPage />,
      },
    ],
  },
]);
