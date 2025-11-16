import { Card, CardContent, CardFooter } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { ShoppingCart, Package, AlertCircle } from 'lucide-react';
import type { Product } from '../types';
import { parseAllergens, formatAllergen } from '../utils/allergens';

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const allergensList = parseAllergens(product.Allergens);
  const isOutOfStock = product.Quantity === 0;

  // Generate initials from product name
  const getInitials = (name: string) => {
    const words = name.split(' ').filter(word => word.length > 0);
    if (words.length === 1) {
      return words[0].substring(0, 2).toUpperCase();
    }
    return words.slice(0, 2).map(word => word[0]).join('').toUpperCase();
  };

  return (
    <Card className="group h-full flex flex-col overflow-hidden hover:border-black transition-all duration-200 bg-white">
      {/* Product Image/Initials */}
      <div className="relative w-full aspect-square overflow-hidden border-b">
        {product.imageUrl ? (
          <img
            src={product.imageUrl}
            alt={product.Product_name}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-50">
            <span className="text-black font-light text-7xl select-none tracking-wider">
              {getInitials(product.Product_name)}
            </span>
          </div>
        )}
      </div>

      {/* Product Details */}
      <CardContent className="flex-1 p-6 space-y-4">
        <div className="space-y-1">
          <h3 className="font-medium text-base leading-tight line-clamp-2">
            {product.Product_name}
          </h3>
          <p className="text-sm text-gray-500">
            {product.Quantity} in stock
          </p>
        </div>

        {/* Allergens - Only show if present */}
        {allergensList.length > 0 && (
          <div className="pt-2 border-t">
            <p className="text-xs text-gray-400 mb-2">Contains allergens</p>
          </div>
        )}
      </CardContent>

      {/* Footer with Price and Action */}
      <CardFooter className="p-6 pt-0 flex items-center justify-between gap-4">
        <div>
          <p className="text-2xl font-normal text-black">${product.Price.toFixed(2)}</p>
        </div>
        <Button
          onClick={() => onAddToCart?.(product)}
          disabled={isOutOfStock}
          variant="outline"
          size="sm"
          className="border-black text-black hover:bg-black hover:text-white transition-colors"
        >
          {isOutOfStock ? 'Out of Stock' : 'Add to Cart'}
        </Button>
      </CardFooter>
    </Card>
  );
}
