export interface Product {
  ProductID: number;
  ProducerID: string | number;
  Product_name: string;
  Price: number;
  Quantity: number;
  Allergens: string; // Comma-separated string from API
  Non_allergens: string; // Comma-separated string from API
  Prediction_score?: number;
  imageUrl?: string; // Optional since API doesn't provide images
}

export interface ProductsState {
  products: Product[];
  isLoading: boolean;
  error: string | null;
  selectedProduct: Product | null;
}

export interface ProductFilters {
  search?: string;
  allergens?: string[];
  minPrice?: number;
  maxPrice?: number;
}
