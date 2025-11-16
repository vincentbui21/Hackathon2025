import { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2, Trash2, AlertCircle } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Input } from '@/shared/components/ui/input';
import { Card } from '@/shared/components/ui/card';
import { chatService } from '../services/chat.service';
import type { Message } from '../types/chat.types';

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: 'Hello! How can I help you today?',
      sender: 'assistant',
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputValue,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await chatService.sendMessage(inputValue);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: response.Answers,
        sender: 'assistant',
        timestamp: new Date(),
        productOptions: response.Options,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError('Failed to send message. Please try again.');
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearConversation = async () => {
    try {
      await chatService.clearConversation();
      setMessages([
        {
          id: '1',
          text: 'Hello! How can I help you today?',
          sender: 'assistant',
          timestamp: new Date(),
        },
      ]);
      setError(null);
    } catch (err) {
      setError('Failed to clear conversation. Please try again.');
      console.error('Clear conversation error:', err);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card className="flex flex-col h-full">
      <div className="p-4 border-b flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">Chat Support</h2>
          <p className="text-sm text-muted-foreground">
            Ask us anything about your orders
          </p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleClearConversation}
          title="Clear conversation"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.sender === 'user' ? 'flex-row-reverse' : 'flex-row'
              }`}
            >
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                {message.sender === 'user' ? (
                  <User className="h-4 w-4" />
                ) : (
                  <Bot className="h-4 w-4" />
                )}
              </div>
              <div
                className={`flex flex-col gap-1 max-w-[80%] ${
                  message.sender === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`rounded-lg px-4 py-2 ${
                    message.sender === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted'
                  }`}
                >
                  <p className="text-sm">{message.text}</p>
                  {message.productOptions && message.productOptions.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-border">
                      <p className="text-xs font-semibold mb-1">Product Recommendations:</p>
                      <div className="flex flex-wrap gap-1">
                        {message.productOptions.map((productId) => (
                          <span
                            key={productId}
                            className="inline-block px-2 py-1 text-xs bg-background/50 rounded"
                          >
                            Product #{productId}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </span>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center flex-shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="flex items-center gap-2 bg-muted rounded-lg px-4 py-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <p className="text-sm">Thinking...</p>
              </div>
            </div>
          )}
          {error && (
            <div className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-destructive/10 flex items-center justify-center flex-shrink-0">
                <AlertCircle className="h-4 w-4 text-destructive" />
              </div>
              <div className="bg-destructive/10 text-destructive rounded-lg px-4 py-2">
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="p-4 border-t">
        <div className="flex gap-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1"
            disabled={isLoading}
          />
          <Button onClick={handleSendMessage} size="icon" disabled={isLoading || !inputValue.trim()}>
            {isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </Card>
  );
}
