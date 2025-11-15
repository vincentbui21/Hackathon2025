import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ProductList } from '../components';
import { useProducts } from '../hooks';
import { useCart } from '@/features/cart';
import { useBookingsStore } from '../store';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { Input } from '@/shared/components/ui/input';
import { ShoppingCart, Search, Package2 } from 'lucide-react';
import { toast } from 'sonner';

export function BookingsPage() {
  const navigate = useNavigate();
  const { products, isLoading, error } = useProducts();
  const { addItem, totalItems, totalPrice } = useCart();
  const { setFilters } = useBookingsStore();
  const [searchQuery, setSearchQuery] = useState('');

  const handleAddToCart = (product: any) => {
    addItem(product);
    toast.success(`${product.Product_name} added to cart!`);
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setFilters({ search: value });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Hero Header */}
      <div className="bg-white border-b shadow-sm">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary flex items-center justify-center">
                <Package2 className="w-6 h-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-3xl font-bold tracking-tight">Premium Ingredients</h1>
                <p className="text-muted-foreground">
                  Curated selection of high-quality products for your business
                </p>
              </div>
            </div>

            {/* Cart Button */}
            <Button
              onClick={() => navigate('/checkout')}
              size="lg"
              className="relative gap-2 shadow-lg"
            >
              <ShoppingCart className="w-5 h-5" />
              <span className="font-semibold">Cart</span>
              {totalItems > 0 && (
                <>
                  <div className="absolute -top-2 -right-2 flex gap-1">
                    <Badge className="rounded-full h-6 min-w-6 px-2 flex items-center justify-center bg-red-500 hover:bg-red-600">
                      {totalItems}
                    </Badge>
                  </div>
                  <span className="text-sm font-normal ml-1 hidden md:inline">
                    ${totalPrice.toFixed(2)}
                  </span>
                </>
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row gap-4 items-center">
            {/* Search Bar */}
            <div className="relative flex-1 w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search products by name, ID, or producer..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10 h-12 text-base shadow-sm"
              />
            </div>

            {/* Results Count */}
            <div className="text-sm text-muted-foreground whitespace-nowrap">
              {!isLoading && (
                <span className="font-medium">
                  {products.length} {products.length === 1 ? 'product' : 'products'}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Product List */}
      <div className="container mx-auto px-4 py-8">
        <ProductList
          products={products}
          isLoading={isLoading}
          error={error}
          onAddToCart={handleAddToCart}
        />
      </div>
    </div>
  );
}
