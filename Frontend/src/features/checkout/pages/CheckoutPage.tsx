import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '@/features/cart';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { Separator } from '@/shared/components/ui/separator';
import { ArrowLeft, Loader2, ShoppingCart, AlertTriangle, Trash2, Minus, Plus } from 'lucide-react';
import { ProductWarningCard } from '../components/ProductWarningCard';
import { CheckoutSummary } from '../components/CheckoutSummary';
import { mlReliabilityService, warningBuilderService } from '../services';
import { toast } from 'sonner';

export function CheckoutPage() {
  const navigate = useNavigate();
  const { items, removeItem, updateQuantity, updateWarnings, warningCount } = useCart();
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [analysisComplete, setAnalysisComplete] = useState(false);
  const hasAnalyzed = useRef(false);

  useEffect(() => {
    const runReliabilityCheck = async () => {
      // Prevent duplicate runs in Strict Mode
      if (hasAnalyzed.current) return;
      hasAnalyzed.current = true;

      if (items.length === 0) {
        setIsAnalyzing(false);
        setAnalysisComplete(true);
        return;
      }

      try {
        setIsAnalyzing(true);

        // Extract product IDs
        const productIds = items.map((item) => item.ProductID);

        // Call ML service
        const response = await mlReliabilityService.predictReliability(productIds);

        // Build warnings from predictions
        const warnings = warningBuilderService.buildWarningsFromPredictions(response.predictions);

        // Create a map of productId -> warning
        const warningsMap = new Map();
        warnings.forEach((warning) => {
          warningsMap.set(warning.productId, warning);
        });

        // Update cart with warnings
        updateWarnings(warningsMap);

        setAnalysisComplete(true);

        if (warnings.length > 0) {
          toast.warning(`Found ${warnings.length} product reliability concern${warnings.length > 1 ? 's' : ''}`);
        } else {
          toast.success('All products passed reliability check');
        }
      } catch (error) {
        console.error('Failed to analyze products:', error);
        toast.error('Failed to analyze product reliability');
      } finally {
        setIsAnalyzing(false);
      }
    };

    runReliabilityCheck();
  }, []); // Only run on mount

  if (items.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="container mx-auto px-4 py-8">
          <Card className="max-w-2xl mx-auto text-center p-12">
            <div className="mb-6">
              <div className="w-20 h-20 rounded-full bg-gray-100 flex items-center justify-center mx-auto mb-4">
                <ShoppingCart className="w-10 h-10 text-gray-400" />
              </div>
              <h2 className="text-2xl font-bold mb-2">Your cart is empty</h2>
              <p className="text-muted-foreground">Add some products to get started!</p>
            </div>
            <Button onClick={() => navigate('/bookings')} className="gap-2">
              <ArrowLeft className="w-4 h-4" />
              Browse Products
            </Button>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-6">
          <Button variant="ghost" onClick={() => navigate('/bookings')} className="gap-2 mb-4">
            <ArrowLeft className="w-4 h-4" />
            Continue Shopping
          </Button>
          <h1 className="text-4xl font-bold mb-2">Checkout</h1>
          <p className="text-muted-foreground">Review your order and product reliability</p>
        </div>

        {/* Analysis Banner */}
        {isAnalyzing && (
          <Card className="mb-6 bg-blue-50 border-blue-200">
            <CardContent className="py-4">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
                <div>
                  <p className="font-semibold text-blue-900">Analyzing Product Reliability...</p>
                  <p className="text-sm text-blue-700">
                    Running ML analysis on {items.length} product{items.length > 1 ? 's' : ''}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Warnings Summary */}
        {analysisComplete && warningCount > 0 && (
          <Card className="mb-6 bg-amber-50 border-amber-200">
            <CardContent className="py-4">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <p className="font-semibold text-amber-900">
                    {warningCount} Product{warningCount > 1 ? 's' : ''} Need{warningCount === 1 ? 's' : ''} Your Attention
                  </p>
                  <p className="text-sm text-amber-700">
                    Our ML system detected potential reliability issues with some products. Review details below.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Items in Cart ({items.length})</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {items.map((item) => (
                  <div key={item.ProductID} className="space-y-3">
                    <div className="flex gap-4">
                      {/* Product Details */}
                      <div className="flex-1 min-w-0">
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <h3 className="font-semibold">{item.Product_name}</h3>
                              {item.warning && (
                                <Badge variant="destructive" className="text-xs">
                                  {item.warning.severity}
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">
                              ID: {item.ProductID} • {item.ProducerID}
                            </p>
                          </div>
                          <button
                            onClick={() => removeItem(item.ProductID)}
                            className="text-red-500 hover:text-red-700 transition-colors"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        </div>

                        {/* Allergens */}
                        {item.Allergens.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-2">
                            {item.Allergens.map((allergen) => (
                              <Badge key={allergen} variant="destructive" className="text-xs">
                                {allergen}
                              </Badge>
                            ))}
                          </div>
                        )}

                        {/* Price and Quantity */}
                        <div className="flex items-center justify-between mt-3">
                          <div className="flex items-center gap-2">
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateQuantity(item.ProductID, item.quantity - 1)}
                              className="h-8 w-8 p-0"
                            >
                              <Minus className="w-3 h-3" />
                            </Button>
                            <span className="w-8 text-center font-medium">{item.quantity}</span>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => updateQuantity(item.ProductID, item.quantity + 1)}
                              className="h-8 w-8 p-0"
                            >
                              <Plus className="w-3 h-3" />
                            </Button>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-primary">
                              ${(item.Price * item.quantity).toFixed(2)}
                            </p>
                            <p className="text-sm text-muted-foreground">${item.Price.toFixed(2)} each</p>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Warning Card */}
                    {item.warning && analysisComplete && (
                      <ProductWarningCard warning={item.warning} productName={item.Product_name} />
                    )}

                    <Separator />
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          {/* Checkout Summary */}
          <div className="space-y-4">
            <CheckoutSummary items={items} />

            <Button
              className="w-full"
              size="lg"
              disabled={isAnalyzing}
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Proceed to Payment'
              )}
            </Button>

            <p className="text-xs text-center text-muted-foreground">
              By placing this order, you agree to our terms and conditions
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
