import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Product, ProductFilters } from '../types';

interface BookingsState {
  products: Product[];
  filteredProducts: Product[];
  isLoading: boolean;
  error: string | null;
  filters: ProductFilters;

  // Actions
  setProducts: (products: Product[]) => void;
  setLoading: (isLoading: boolean) => void;
  setError: (error: string | null) => void;
  setFilters: (filters: ProductFilters) => void;
  applyFilters: () => void;
  clearFilters: () => void;
}

export const useBookingsStore = create<BookingsState>()(
  devtools(
    (set, get) => ({
      products: [],
      filteredProducts: [],
      isLoading: false,
      error: null,
      filters: {},

      setProducts: (products) => {
        set({ products, filteredProducts: products });
        get().applyFilters();
      },

      setLoading: (isLoading) => set({ isLoading }),

      setError: (error) => set({ error, isLoading: false }),

      setFilters: (filters) => {
        set({ filters });
        get().applyFilters();
      },

      applyFilters: () => {
        const { products, filters } = get();
        let filtered = [...products];

        // Search filter
        if (filters.search) {
          const searchLower = filters.search.toLowerCase();
          filtered = filtered.filter((product) =>
            product.Product_name.toLowerCase().includes(searchLower) ||
            product.ProductID.toLowerCase().includes(searchLower) ||
            product.ProducerID.toLowerCase().includes(searchLower)
          );
        }

        // Allergen filter
        if (filters.allergens && filters.allergens.length > 0) {
          filtered = filtered.filter((product) =>
            !filters.allergens!.some((allergen) =>
              product.Allergens.includes(allergen)
            )
          );
        }

        // Price range filter
        if (filters.minPrice !== undefined) {
          filtered = filtered.filter((product) => product.Price >= filters.minPrice!);
        }
        if (filters.maxPrice !== undefined) {
          filtered = filtered.filter((product) => product.Price <= filters.maxPrice!);
        }

        set({ filteredProducts: filtered });
      },

      clearFilters: () => {
        set({ filters: {}, filteredProducts: get().products });
      },
    }),
    { name: 'bookings-store' }
  )
);
