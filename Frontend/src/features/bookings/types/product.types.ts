export interface Product {
  ProductID: number;
  ProducerID: string;
  Product_name: string;
  Price: number;
  Quantity: number;
  Allergens: string[];
  Non_allergens: string[];
  imageUrl: string;
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
