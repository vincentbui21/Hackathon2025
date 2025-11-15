import { apiClient, API_ENDPOINTS } from '@/core/api';
import type { Product } from '../types';

// Mock data for development - remove when backend is ready
const MOCK_PRODUCTS: Product[] = [
  {
    ProductID: 101,
    ProducerID: 'PROD-001',
    Product_name: 'Organic Tomatoes',
    Price: 4.99,
    Quantity: 150,
    Allergens: [],
    Non_allergens: ['Gluten', 'Dairy', 'Nuts'],
    imageUrl: 'https://images.unsplash.com/photo-1546470427-e26264be0b93?w=500&h=500&fit=crop',
  },
  {
    ProductID: 102,
    ProducerID: 'PROD-002',
    Product_name: 'Fresh Mozzarella',
    Price: 8.50,
    Quantity: 80,
    Allergens: ['Dairy'],
    Non_allergens: ['Gluten', 'Nuts', 'Soy'],
    imageUrl: 'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=500&h=500&fit=crop',
  },
  {
    ProductID: 103,
    ProducerID: 'PROD-001',
    Product_name: 'Whole Wheat Flour',
    Price: 3.25,
    Quantity: 200,
    Allergens: ['Gluten'],
    Non_allergens: ['Dairy', 'Nuts', 'Eggs'],
    imageUrl: 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b?w=500&h=500&fit=crop',
  },
  {
    ProductID: 104,
    ProducerID: 'PROD-003',
    Product_name: 'Extra Virgin Olive Oil',
    Price: 12.99,
    Quantity: 60,
    Allergens: [],
    Non_allergens: ['Gluten', 'Dairy', 'Nuts', 'Soy'],
    imageUrl: 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=500&h=500&fit=crop',
  },
  {
    ProductID: 105,
    ProducerID: 'PROD-004',
    Product_name: 'Almond Butter',
    Price: 9.75,
    Quantity: 45,
    Allergens: ['Nuts'],
    Non_allergens: ['Gluten', 'Dairy', 'Soy'],
    imageUrl: 'https://images.unsplash.com/photo-1520803483588-2c8a8a7ccffa?w=500&h=500&fit=crop',
  },
  {
    ProductID: 106,
    ProducerID: 'PROD-002',
    Product_name: 'Free-Range Eggs',
    Price: 5.50,
    Quantity: 120,
    Allergens: ['Eggs'],
    Non_allergens: ['Gluten', 'Dairy', 'Nuts'],
    imageUrl: 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=500&h=500&fit=crop',
  },
  {
    ProductID: 107,
    ProducerID: 'PROD-005',
    Product_name: 'Sourdough Bread',
    Price: 6.25,
    Quantity: 90,
    Allergens: ['Gluten'],
    Non_allergens: ['Dairy', 'Nuts', 'Eggs'],
    imageUrl: 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=500&h=500&fit=crop',
  },
  {
    ProductID: 108,
    ProducerID: 'PROD-003',
    Product_name: 'Greek Yogurt',
    Price: 4.75,
    Quantity: 110,
    Allergens: ['Dairy'],
    Non_allergens: ['Gluten', 'Nuts', 'Soy'],
    imageUrl: 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500&h=500&fit=crop',
  },
];

const USE_MOCK_DATA = true; // Toggle this when backend is ready

class BookingsService {
  async getAllProducts(): Promise<Product[]> {
    if (USE_MOCK_DATA) {
      // Simulate network delay
      await new Promise((resolve) => setTimeout(resolve, 800));
      return MOCK_PRODUCTS;
    }

    return apiClient.get<Product[]>(API_ENDPOINTS.PRODUCTS);
  }

  async getProductById(id: number): Promise<Product | null> {
    if (USE_MOCK_DATA) {
      await new Promise((resolve) => setTimeout(resolve, 300));
      return MOCK_PRODUCTS.find((p) => p.ProductID === id) || null;
    }

    return apiClient.get<Product>(API_ENDPOINTS.PRODUCT_BY_ID(id.toString()));
  }

  async searchProducts(query: string): Promise<Product[]> {
    if (USE_MOCK_DATA) {
      await new Promise((resolve) => setTimeout(resolve, 400));
      const queryLower = query.toLowerCase();
      return MOCK_PRODUCTS.filter((p) =>
        p.Product_name.toLowerCase().includes(queryLower) ||
        p.ProductID.toLowerCase().includes(queryLower)
      );
    }

    return apiClient.get<Product[]>(`${API_ENDPOINTS.PRODUCTS}?search=${query}`);
  }
}

export const bookingsService = new BookingsService();
