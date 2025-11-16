import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import {
  Package2,
  ShoppingCart,
  TrendingUp,
  DollarSign,
  ArrowUpRight,
  ArrowDownRight,
  Users,
  Activity
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

// Mock data - replace with real data from your API
const stats = [
  {
    title: 'Total Revenue',
    value: '$45,231.89',
    change: '+20.1%',
    changeType: 'positive' as const,
    icon: DollarSign,
    description: 'from last month',
  },
  {
    title: 'Orders',
    value: '2,350',
    change: '+180',
    changeType: 'positive' as const,
    icon: ShoppingCart,
    description: 'this month',
  },
  {
    title: 'Products',
    value: '154',
    change: '+12',
    changeType: 'positive' as const,
    icon: Package2,
    description: 'active products',
  },
  {
    title: 'Avg. Order Value',
    value: '$19.25',
    change: '-4.3%',
    changeType: 'negative' as const,
    icon: TrendingUp,
    description: 'from last month',
  },
];

const recentOrders = [
  { id: 'ORD-001', customer: 'John Doe', product: 'Premium Truffle Oil', amount: '$45.00', status: 'completed', date: '2025-11-14' },
  { id: 'ORD-002', customer: 'Jane Smith', product: 'Organic Vanilla Extract', amount: '$28.50', status: 'processing', date: '2025-11-14' },
  { id: 'ORD-003', customer: 'Bob Johnson', product: 'Himalayan Pink Salt', amount: '$15.99', status: 'completed', date: '2025-11-13' },
  { id: 'ORD-004', customer: 'Alice Williams', product: 'Extra Virgin Olive Oil', amount: '$32.00', status: 'pending', date: '2025-11-13' },
  { id: 'ORD-005', customer: 'Charlie Brown', product: 'Saffron Threads', amount: '$89.99', status: 'completed', date: '2025-11-12' },
];

const topProducts = [
  { name: 'Premium Truffle Oil', sales: 145, revenue: '$6,525' },
  { name: 'Organic Vanilla Extract', sales: 112, revenue: '$3,192' },
  { name: 'Himalayan Pink Salt', sales: 98, revenue: '$1,567' },
  { name: 'Extra Virgin Olive Oil', sales: 87, revenue: '$2,784' },
];

export function DashboardPage() {
  const navigate = useNavigate();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 hover:bg-green-100';
      case 'processing':
        return 'bg-blue-100 text-blue-800 hover:bg-blue-100';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100';
      default:
        return 'bg-gray-100 text-gray-800 hover:bg-gray-100';
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Welcome back! Here's what's happening with your store today.
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => navigate('/orders')}>
            <Activity className="w-4 h-4 mr-2" />
            View All Orders
          </Button>
          <Button onClick={() => navigate('/booking')}>
            <Package2 className="w-4 h-4 mr-2" />
            Browse Products
          </Button>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title}>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">
                  {stat.title}
                </CardTitle>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="flex items-center gap-1 mt-1">
                  {stat.changeType === 'positive' ? (
                    <ArrowUpRight className="h-4 w-4 text-green-600" />
                  ) : (
                    <ArrowDownRight className="h-4 w-4 text-red-600" />
                  )}
                  <span
                    className={`text-xs font-medium ${
                      stat.changeType === 'positive'
                        ? 'text-green-600'
                        : 'text-red-600'
                    }`}
                  >
                    {stat.change}
                  </span>
                  <span className="text-xs text-muted-foreground ml-1">
                    {stat.description}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        {/* Recent Orders */}
        <Card className="col-span-full lg:col-span-4">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Recent Orders</CardTitle>
                <CardDescription>
                  Latest orders from your customers
                </CardDescription>
              </div>
              <Button variant="ghost" size="sm" onClick={() => navigate('/orders')}>
                View All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentOrders.map((order) => (
                <div
                  key={order.id}
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-accent/50 transition-colors cursor-pointer"
                  onClick={() => navigate('/orders')}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <p className="text-sm font-medium">{order.id}</p>
                      <Badge className={getStatusColor(order.status)}>
                        {order.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {order.customer}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {order.product}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">{order.amount}</p>
                    <p className="text-xs text-muted-foreground">{order.date}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Top Products */}
        <Card className="col-span-full lg:col-span-3">
          <CardHeader>
            <CardTitle>Top Products</CardTitle>
            <CardDescription>
              Best performing products this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topProducts.map((product, index) => (
                <div key={product.name} className="flex items-center gap-4">
                  <div className="flex items-center justify-center w-8 h-8 rounded-full bg-primary/10 text-primary font-semibold text-sm">
                    {index + 1}
                  </div>
                  <div className="flex-1 space-y-1">
                    <p className="text-sm font-medium leading-none">
                      {product.name}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {product.sales} sales
                    </p>
                  </div>
                  <div className="text-sm font-semibold">
                    {product.revenue}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 gap-2"
              onClick={() => navigate('/booking')}
            >
              <Package2 className="h-5 w-5" />
              <div className="text-left">
                <p className="font-semibold">Browse Products</p>
                <p className="text-xs text-muted-foreground">
                  View all available products
                </p>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 gap-2"
              onClick={() => navigate('/orders')}
            >
              <ShoppingCart className="h-5 w-5" />
              <div className="text-left">
                <p className="font-semibold">Manage Orders</p>
                <p className="text-xs text-muted-foreground">
                  View and process orders
                </p>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 gap-2"
              onClick={() => navigate('/checkout')}
            >
              <DollarSign className="h-5 w-5" />
              <div className="text-left">
                <p className="font-semibold">Checkout</p>
                <p className="text-xs text-muted-foreground">
                  Process new order
                </p>
              </div>
            </Button>
            <Button
              variant="outline"
              className="h-auto flex-col items-start p-4 gap-2"
            >
              <Users className="h-5 w-5" />
              <div className="text-left">
                <p className="font-semibold">Customers</p>
                <p className="text-xs text-muted-foreground">
                  Manage customer database
                </p>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
