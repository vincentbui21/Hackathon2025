import { ProductCard } from './ProductCard';
import type { Product } from '../types';
import { Loader2, Package, Search } from 'lucide-react';

interface ProductListProps {
  products: Product[];
  isLoading?: boolean;
  error?: string | null;
  onAddToCart?: (product: Product) => void;
}

export function ProductList({ products, isLoading, error, onAddToCart }: ProductListProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <Loader2 className="w-16 h-16 animate-spin text-primary mb-4" />
        <p className="text-lg font-medium text-muted-foreground">Loading premium products...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <div className="w-20 h-20 rounded-full bg-red-50 flex items-center justify-center mb-4">
          <Package className="w-10 h-10 text-red-600" />
        </div>
        <h3 className="text-2xl font-bold mb-2">Failed to load products</h3>
        <p className="text-muted-foreground text-center max-w-md">{error}</p>
      </div>
    );
  }

  if (products.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-32">
        <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mb-4">
          <Search className="w-10 h-10 text-gray-400" />
        </div>
        <h3 className="text-2xl font-bold mb-2">No products found</h3>
        <p className="text-muted-foreground">Try adjusting your search or filters</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
      {products.map((product) => (
        <ProductCard key={product.ProductID} product={product} onAddToCart={onAddToCart} />
      ))}
    </div>
  );
}
