import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';
import { bookingsService } from '../services';
import { useBookingsStore } from '../store';

export function useProducts() {
  const { setProducts, setLoading, setError, filteredProducts, isLoading, error } = useBookingsStore();

  const query = useQuery({
    queryKey: ['products'],
    queryFn: () => bookingsService.getAllProducts(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 2,
  });

  useEffect(() => {
    if (query.isLoading) {
      setLoading(true);
    } else if (query.error) {
      setError(query.error instanceof Error ? query.error.message : 'Failed to fetch products');
    } else if (query.data) {
      setProducts(query.data);
      setLoading(false);
    }
  }, [query.isLoading, query.error, query.data, setProducts, setLoading, setError]);

  return {
    products: filteredProducts,
    isLoading: isLoading || query.isLoading,
    error: error || (query.error instanceof Error ? query.error.message : null),
    refetch: query.refetch,
  };
}
