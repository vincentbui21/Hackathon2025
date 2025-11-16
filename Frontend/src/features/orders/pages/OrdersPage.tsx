import { useOrders, useOrderImageUpload } from '../hooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Badge } from '@/shared/components/ui/badge';
import { Skeleton } from '@/shared/components/ui/skeleton';
import { Button } from '@/shared/components/ui/button';
import { FileText, Package, Clock, CheckCircle, XCircle, AlertCircle, Upload, ImageIcon, Loader2, X } from 'lucide-react';

const statusConfig: Record<string, {
  label: string;
  variant: 'secondary' | 'default' | 'destructive';
  icon: any;
  color: string;
}> = {
  Pending: {
    label: 'Pending',
    variant: 'secondary',
    icon: Clock,
    color: 'text-gray-600',
  },
  pending: {
    label: 'Pending',
    variant: 'secondary',
    icon: Clock,
    color: 'text-gray-600',
  },
  Shipped: {
    label: 'Shipped',
    variant: 'default',
    icon: AlertCircle,
    color: 'text-blue-600',
  },
  processing: {
    label: 'Processing',
    variant: 'default',
    icon: AlertCircle,
    color: 'text-blue-600',
  },
  Delivered: {
    label: 'Delivered',
    variant: 'default',
    icon: CheckCircle,
    color: 'text-green-600',
  },
  completed: {
    label: 'Completed',
    variant: 'default',
    icon: CheckCircle,
    color: 'text-green-600',
  },
  cancelled: {
    label: 'Cancelled',
    variant: 'destructive',
    icon: XCircle,
    color: 'text-red-600',
  },
};

export function OrdersPage() {
  const { data: orders, isLoading, error } = useOrders();
  const { orderImages, fileInputRefs, handleFileSelect, handleSendImage, clearImage } = useOrderImageUpload();

  if (isLoading) {
    return (
      <div>
        <div className="mb-6">
          <Skeleton className="h-10 w-48 mb-2" />
          <Skeleton className="h-5 w-96" />
        </div>
        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <Skeleton className="h-6 w-full mb-4" />
                <Skeleton className="h-4 w-3/4 mb-2" />
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div>
        <Card className="max-w-2xl mx-auto text-center p-12">
          <div className="mb-6">
            <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <XCircle className="w-10 h-10 text-red-600" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Failed to load orders</h2>
            <p className="text-muted-foreground">{error.message}</p>
          </div>
        </Card>
      </div>
    );
  }

  if (!orders || orders.length === 0) {
    return (
      <div>
        <Card className="max-w-2xl mx-auto text-center p-12">
          <div className="mb-6">
            <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
              <FileText className="w-10 h-10 text-gray-400" />
            </div>
            <h2 className="text-2xl font-bold mb-2">No orders yet</h2>
            <p className="text-muted-foreground">Your orders will appear here once you place them.</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-4xl font-bold mb-2">Orders</h1>
        <p className="text-muted-foreground">View and track your order history</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {orders.map((order) => {
          const statusInfo = statusConfig[order.Status] || statusConfig.pending;
          const StatusIcon = statusInfo.icon;

          // Handle tracking items (could be array of objects or arrays)
          const trackingItems = Array.isArray(order.Tracking)
            ? order.Tracking.map((item) => {
                if (Array.isArray(item)) {
                  return {
                    product_id: item[0],
                    ordered_quantity: item[1],
                    real_quantity: item[2] || item[1],
                  };
                }
                return item;
              })
            : [];

          return (
            <Card key={order.OrderID} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                      <Package className="w-5 h-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle className="text-lg mb-1">
                        Order #{order.OrderID}
                      </CardTitle>
                      <p className="text-sm text-muted-foreground">
                        {trackingItems.length} item{trackingItems.length !== 1 ? 's' : ''}
                      </p>
                    </div>
                  </div>
                  <Badge variant={statusInfo.variant} className="gap-1">
                    <StatusIcon className="w-3 h-3" />
                    {statusInfo.label}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {/* Order Items */}
                  {trackingItems.length > 0 && (
                    <div className="border-t pt-3">
                      <h4 className="text-sm font-semibold mb-2">Items ({trackingItems.length})</h4>
                      <div className="space-y-2">
                        {trackingItems.map((item, idx) => (
                          <div
                            key={idx}
                            className="flex justify-between items-center text-sm"
                          >
                            <div className="flex items-center gap-2">
                              <span className="text-muted-foreground">{item.ordered_quantity}x</span>
                              <span>Product #{item.product_id}</span>
                            </div>
                            {item.real_quantity !== item.ordered_quantity && (
                              <Badge variant="secondary" className="text-xs">
                                Received: {item.real_quantity}
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Total */}
                  <div className="border-t pt-3 flex justify-between items-center">
                    <span className="font-semibold">Total Amount</span>
                    <span className="text-xl font-bold text-primary">
                      ${order.Total.toFixed(2)}
                    </span>
                  </div>

                  {/* Image Upload Section */}
                  <div className="border-t pt-4 mt-2">
                    <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                      <ImageIcon className="w-4 h-4" />
                      Upload Delivery Image
                    </h4>

                    <div className="space-y-3">
                      {/* Image Preview */}
                      {orderImages[order.OrderID]?.preview && (
                        <div className="relative inline-block">
                          <img
                            src={orderImages[order.OrderID].preview!}
                            alt="Order preview"
                            className="w-full max-w-xs h-48 object-cover rounded-lg border-2 border-gray-200"
                          />
                          <button
                            onClick={() => clearImage(order.OrderID)}
                            className="absolute top-2 right-2 bg-white rounded-full p-1 shadow-md hover:bg-gray-100 transition-colors"
                            disabled={orderImages[order.OrderID]?.uploading}
                          >
                            <X className="w-4 h-4 text-gray-600" />
                          </button>
                        </div>
                      )}

                      {/* Upload Controls */}
                      <div className="flex items-center gap-2">
                        <input
                          ref={(el) => (fileInputRefs.current[order.OrderID] = el)}
                          type="file"
                          accept="image/*"
                          onChange={(e) => handleFileSelect(order.OrderID, e.target.files?.[0] || null)}
                          className="hidden"
                          id={`file-input-${order.OrderID}`}
                        />

                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => document.getElementById(`file-input-${order.OrderID}`)?.click()}
                          disabled={orderImages[order.OrderID]?.uploading}
                          className="gap-2"
                        >
                          <Upload className="w-4 h-4" />
                          {orderImages[order.OrderID]?.preview ? 'Change Image' : 'Select Image'}
                        </Button>

                        {orderImages[order.OrderID]?.file && (
                          <Button
                            size="sm"
                            onClick={() => handleSendImage(order.OrderID)}
                            disabled={orderImages[order.OrderID]?.uploading}
                            className="gap-2"
                          >
                            {orderImages[order.OrderID]?.uploading ? (
                              <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Sending...
                              </>
                            ) : (
                              <>
                                <CheckCircle className="w-4 h-4" />
                                Send
                              </>
                            )}
                          </Button>
                        )}
                      </div>

                      {/* Status Messages */}
                      {orderImages[order.OrderID]?.error && (
                        <div className="flex items-center gap-2 text-sm text-red-600 bg-red-50 p-2 rounded">
                          <XCircle className="w-4 h-4 flex-shrink-0" />
                          <span>{orderImages[order.OrderID].error}</span>
                        </div>
                      )}

                      {orderImages[order.OrderID]?.success && (
                        <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 p-2 rounded">
                          <CheckCircle className="w-4 h-4 flex-shrink-0" />
                          <span>Image uploaded successfully!</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
