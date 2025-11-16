import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/components/ui/dialog';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { Loader2, AlertCircle, ArrowRight } from 'lucide-react';
import { substitutionService } from '../services';
import { parseAllergens } from '@/features/bookings/utils/allergens';
import type { Product } from '@/features/bookings/types';

interface SubstitutionModalProps {
  isOpen: boolean;
  onClose: () => void;
  product: Product;
  onSelectSubstitute: (substitute: Product) => void;
}

export function SubstitutionModal({
  isOpen,
  onClose,
  product,
  onSelectSubstitute,
}: SubstitutionModalProps) {
  const [substitutes, setSubstitutes] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadSubstitutes();
    }
  }, [isOpen, product.ProductID]);

  const loadSubstitutes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await substitutionService.getSubstitutes(product.ProductID);
      setSubstitutes(data || []);
    } catch (err: any) {
      setError(err.message || 'Failed to load substitutes');
      setSubstitutes([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectSubstitute = (substitute: Product) => {
    onSelectSubstitute(substitute);
    onClose();
  };

  // Generate initials from product name
  const getInitials = (name: string) => {
    const words = name.split(' ').filter(word => word.length > 0);
    if (words.length === 1) {
      return words[0].substring(0, 2).toUpperCase();
    }
    return words.slice(0, 2).map(word => word[0]).join('').toUpperCase();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Find Better Alternatives</DialogTitle>
          <DialogDescription>
            We found these high-quality substitutes for <strong>{product.Product_name}</strong>
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="w-12 h-12 animate-spin text-primary mb-4" />
            <p className="text-sm text-muted-foreground">Finding best substitutes...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center py-12">
            <AlertCircle className="w-12 h-12 text-red-500 mb-4" />
            <p className="text-sm text-red-600">{error}</p>
          </div>
        ) : !substitutes || substitutes.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-sm text-muted-foreground">No substitutes available</p>
          </div>
        ) : (
          <div className="space-y-4 mt-4">
            {substitutes.map((substitute, index) => {
              const allergensList = parseAllergens(substitute.Allergens);

              return (
                <div
                  key={substitute.ProductID}
                  className="border rounded-lg p-4 hover:border-black transition-colors"
                >
                  <div className="flex gap-4">
                    {/* Product Image/Initials */}
                    <div className="w-20 h-20 flex-shrink-0 border rounded-lg overflow-hidden">
                      {substitute.imageUrl ? (
                        <img
                          src={substitute.imageUrl}
                          alt={substitute.Product_name}
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-50">
                          <span className="text-black font-light text-2xl select-none">
                            {getInitials(substitute.Product_name)}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Product Details */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {index === 0 && (
                              <Badge className="bg-green-100 text-green-800 border-green-300">
                                Best Match
                              </Badge>
                            )}
                          </div>
                          <h3 className="font-medium text-base leading-tight">
                            {substitute.Product_name}
                          </h3>
                          <p className="text-sm text-gray-500 mt-1">
                            {substitute.Quantity} in stock
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-2xl font-normal text-black">
                            ${substitute.Price.toFixed(2)}
                          </p>
                          {substitute.Price < product.Price && (
                            <Badge variant="secondary" className="text-xs mt-1">
                              Save ${(product.Price - substitute.Price).toFixed(2)}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {allergensList.length > 0 && (
                        <p className="text-xs text-muted-foreground mb-3">
                          Contains allergens
                        </p>
                      )}

                      <Button
                        onClick={() => handleSelectSubstitute(substitute)}
                        variant="outline"
                        size="sm"
                        className="border-black text-black hover:bg-black hover:text-white w-full sm:w-auto"
                      >
                        Replace with this
                        <ArrowRight className="w-4 h-4 ml-2" />
                      </Button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        <div className="flex justify-end gap-2 mt-6 pt-4 border-t">
          <Button variant="outline" onClick={onClose}>
            Keep Original
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
