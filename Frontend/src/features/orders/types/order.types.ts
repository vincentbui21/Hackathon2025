export interface TrackingItem {
  product_id: number;
  ordered_quantity: number;
  real_quantity: number;
}

export interface SubstitutionItem {
  product_id: number;
  original_quantity: number;
  substituted_quantity: number;
}

export interface Order {
  OrderID: number;
  Total: number;
  Status: string;
  Tracking: TrackingItem[] | number[][];
  Substitution: SubstitutionItem[] | number[][];
}

export interface OrdersResponse {
  orders: Order[];
}

export interface OrdersState {
  orders: Order[];
  isLoading: boolean;
  error: string | null;
  selectedOrder: Order | null;
}
