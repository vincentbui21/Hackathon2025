import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ordersService } from '../services';
import { chatService } from '@/features/chat/services/chat.service';

interface OrderImageState {
  file: File | null;
  preview: string | null;
  uploading: boolean;
  error: string | null;
  success: boolean;
}

interface UseOrderImageUploadReturn {
  orderImages: { [orderId: number]: OrderImageState };
  fileInputRefs: React.MutableRefObject<{ [orderId: number]: HTMLInputElement | null }>;
  handleFileSelect: (orderId: number, file: File | null) => void;
  handleSendImage: (orderId: number) => Promise<void>;
  clearImage: (orderId: number) => void;
}

export function useOrderImageUpload(): UseOrderImageUploadReturn {
  const [orderImages, setOrderImages] = useState<{ [orderId: number]: OrderImageState }>({});
  const fileInputRefs = useRef<{ [orderId: number]: HTMLInputElement | null }>({});
  const navigate = useNavigate();

  const handleFileSelect = useCallback((orderId: number, file: File | null) => {
    if (!file) {
      setOrderImages(prev => ({
        ...prev,
        [orderId]: {
          file: null,
          preview: null,
          uploading: false,
          error: null,
          success: false,
        },
      }));
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setOrderImages(prev => ({
        ...prev,
        [orderId]: {
          file: null,
          preview: null,
          uploading: false,
          error: 'Please select an image file',
          success: false,
        },
      }));
      return;
    }

    // Validate file size (max 10MB)
    const maxSize = 10 * 1024 * 1024;
    if (file.size > maxSize) {
      setOrderImages(prev => ({
        ...prev,
        [orderId]: {
          file: null,
          preview: null,
          uploading: false,
          error: 'Image must be smaller than 10MB',
          success: false,
        },
      }));
      return;
    }

    // Create preview
    const preview = URL.createObjectURL(file);
    setOrderImages(prev => ({
      ...prev,
      [orderId]: {
        file,
        preview,
        uploading: false,
        error: null,
        success: false,
      },
    }));
  }, []);

  const handleSendImage = useCallback(async (orderId: number) => {
    const orderImage = orderImages[orderId];
    if (!orderImage?.file) return;

    setOrderImages(prev => ({
      ...prev,
      [orderId]: {
        ...prev[orderId],
        uploading: true,
        error: null,
      },
    }));

    try {
      const response = await ordersService.validateOrder(orderId, orderImage.file);

      // Check if validation passed
      if (response.validation_passed) {
        setOrderImages(prev => ({
          ...prev,
          [orderId]: {
            ...prev[orderId],
            uploading: false,
            success: true,
          },
        }));

        toast.success('Order validated successfully!', {
          description: 'Your order has been completed.',
        });

        // Clear success message after 3 seconds
        setTimeout(() => {
          setOrderImages(prev => {
            const current = prev[orderId];
            if (current?.success) {
              return {
                ...prev,
                [orderId]: {
                  ...current,
                  success: false,
                },
              };
            }
            return prev;
          });
        }, 3000);
      } else {
        // Validation failed - trigger apology flow
        setOrderImages(prev => ({
          ...prev,
          [orderId]: {
            ...prev[orderId],
            uploading: false,
            success: false,
          },
        }));

        // Get the first product from the order to use for apology
        const firstProduct = response.products_in_order?.[0];
        if (firstProduct) {
          // Extract product ID from tracking data or use a default
          const productId = 1; // You may need to adjust this based on actual data structure
          const amountMissing = firstProduct.quantity || 1;

          // Trigger apology message in chat
          await chatService.triggerOrderApology(productId, amountMissing);
        }

        // Show toast and navigate to chat
        toast.error('Order validation failed', {
          description: 'Some items appear to be missing. Check the chat for assistance.',
          action: {
            label: 'Go to Chat',
            onClick: () => navigate('/chat'),
          },
        });

        // Navigate to chat after a short delay
        setTimeout(() => {
          navigate('/chat');
        }, 2000);
      }
    } catch (err: any) {
      setOrderImages(prev => ({
        ...prev,
        [orderId]: {
          ...prev[orderId],
          uploading: false,
          error: err.message || 'Failed to upload image',
        },
      }));

      toast.error('Upload failed', {
        description: err.message || 'Failed to upload image',
      });
    }
  }, [orderImages, navigate]);

  const clearImage = useCallback((orderId: number) => {
    // Revoke the object URL to free memory
    const orderImage = orderImages[orderId];
    if (orderImage?.preview) {
      URL.revokeObjectURL(orderImage.preview);
    }

    setOrderImages(prev => ({
      ...prev,
      [orderId]: {
        file: null,
        preview: null,
        uploading: false,
        error: null,
        success: false,
      },
    }));

    // Clear the file input
    if (fileInputRefs.current[orderId]) {
      fileInputRefs.current[orderId]!.value = '';
    }
  }, [orderImages]);

  return {
    orderImages,
    fileInputRefs,
    handleFileSelect,
    handleSendImage,
    clearImage,
  };
}
