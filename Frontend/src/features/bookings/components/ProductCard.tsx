import { Card, CardContent, CardFooter } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { ShoppingCart, Package, AlertCircle } from 'lucide-react';
import type { Product } from '../types';

interface ProductCardProps {
  product: Product;
  onAddToCart?: (product: Product) => void;
}

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const hasAllergens = product.Allergens.length > 0;
  const isOutOfStock = product.Quantity === 0;
  const isLowStock = product.Quantity > 0 && product.Quantity < 20;

  return (
    <Card className="group h-full flex flex-col overflow-hidden hover:shadow-xl transition-all duration-300 border-0 shadow-md">
      {/* Product Image */}
      <div className="relative w-full aspect-square overflow-hidden bg-gray-100">
        <img
          src={product.imageUrl}
          alt={product.Product_name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
          loading="lazy"
        />

        {/* Stock Badge */}
        <div className="absolute top-3 right-3 flex flex-col gap-2">
          {isOutOfStock ? (
            <Badge variant="destructive" className="shadow-lg">
              Out of Stock
            </Badge>
          ) : isLowStock ? (
            <Badge className="bg-amber-500 hover:bg-amber-600 shadow-lg">
              <AlertCircle className="w-3 h-3 mr-1" />
              Low Stock
            </Badge>
          ) : (
            <Badge variant="secondary" className="shadow-lg">
              <Package className="w-3 h-3 mr-1" />
              {product.Quantity} in stock
            </Badge>
          )}
        </div>

        {/* Allergen Badge */}
        {hasAllergens && (
          <div className="absolute top-3 left-3">
            <Badge variant="destructive" className="shadow-lg">
              <AlertCircle className="w-3 h-3 mr-1" />
              Contains Allergens
            </Badge>
          </div>
        )}
      </div>

      {/* Product Details */}
      <CardContent className="flex-1 p-4 space-y-3">
        <div>
          <h3 className="font-bold text-lg leading-tight mb-1 line-clamp-2 min-h-[3.5rem]">
            {product.Product_name}
          </h3>
          <p className="text-xs text-muted-foreground">
            Producer: {product.ProducerID}
          </p>
        </div>

        {/* Allergens */}
        {hasAllergens && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Allergens:</p>
            <div className="flex flex-wrap gap-1">
              {product.Allergens.map((allergen) => (
                <Badge key={allergen} variant="outline" className="text-xs border-red-300 text-red-700">
                  {allergen}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Free From */}
        {product.Non_allergens.length > 0 && (
          <div>
            <p className="text-xs font-medium text-muted-foreground mb-1.5">Free From:</p>
            <div className="flex flex-wrap gap-1">
              {product.Non_allergens.slice(0, 3).map((item) => (
                <Badge key={item} variant="outline" className="text-xs border-green-300 text-green-700">
                  {item}
                </Badge>
              ))}
              {product.Non_allergens.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{product.Non_allergens.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}
      </CardContent>

      {/* Footer with Price and Action */}
      <CardFooter className="p-4 pt-0 flex items-end justify-between gap-3">
        <div>
          <p className="text-xs text-muted-foreground mb-0.5">Price per unit</p>
          <p className="text-2xl font-bold text-primary">${product.Price.toFixed(2)}</p>
        </div>
        <Button
          onClick={() => onAddToCart?.(product)}
          disabled={isOutOfStock}
          size="lg"
          className="gap-2"
        >
          <ShoppingCart className="w-4 h-4" />
          {isOutOfStock ? 'Out of Stock' : 'Add'}
        </Button>
      </CardFooter>
    </Card>
  );
}
