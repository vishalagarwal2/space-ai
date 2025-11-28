# TanStack Query Implementation

This document outlines the production-ready TanStack Query implementation for the Lance frontend.

## Overview

We've upgraded from basic axios calls to TanStack Query (React Query) for better:

- **Caching**: Automatic data caching with configurable stale times
- **Background refetching**: Keep data fresh without user interaction
- **Error handling**: Comprehensive error states and retry logic
- **Loading states**: Better UX with proper loading indicators
- **Optimistic updates**: Immediate UI updates with rollback on failure

## Architecture

### 1. QueryClient Setup (`src/lib/providers/QueryProvider.tsx`)

```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      retry: (failureCount, error) => {
        // Don't retry on 4xx errors
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 3;
      },
      retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: (failureCount, error) => {
        if (error?.response?.status >= 400 && error?.response?.status < 500) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});
```

### 2. Custom Hooks (`src/hooks/useConnectedAccounts.ts`)

#### Query Hook - `useConnectedAccounts()`

- Fetches connected accounts with caching
- Automatic background refetching
- Error handling with retry logic

#### Mutation Hooks

- `useInstagramConnection()` - Connect Instagram account
- `useDisconnectAccount()` - Disconnect any account
- Automatic cache invalidation on success

#### Utility Hooks

- `useIsInstagramConnected()` - Derived state for UI logic

### 3. Error Handling (`src/lib/errorHandling.ts`)

Comprehensive error handling with:

- HTTP status code mapping
- User-friendly error messages
- Retry logic for appropriate errors
- Network error detection

### 4. Query Keys (`src/hooks/useConnectedAccounts.ts`)

Structured query keys for consistent cache management:

```typescript
export const connectedAccountsKeys = {
  all: ["connectedAccounts"] as const,
  lists: () => [...connectedAccountsKeys.all, "list"] as const,
  list: (filters: Record<string, unknown>) =>
    [...connectedAccountsKeys.lists(), { filters }] as const,
};
```

## Usage Examples

### Basic Query Usage

```typescript
function MyComponent() {
  const { data: accounts, isLoading, error } = useConnectedAccounts();

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  return <AccountsList accounts={accounts} />;
}
```

### Mutation Usage

```typescript
function ConnectButton() {
  const { mutate: connectInstagram, isPending } = useInstagramConnection();

  return (
    <button
      onClick={() => connectInstagram()}
      disabled={isPending}
    >
      {isPending ? "Connecting..." : "Connect Instagram"}
    </button>
  );
}
```

### Error Handling

```typescript
function MyComponent() {
  const { handleError } = useErrorHandler();

  const handleAction = async () => {
    try {
      await someAsyncOperation();
    } catch (error) {
      handleError(error, "action execution");
    }
  };
}
```

## Benefits

### 1. **Performance**

- Automatic caching reduces API calls
- Background refetching keeps data fresh
- Optimistic updates for better UX

### 2. **Developer Experience**

- Type-safe hooks
- Automatic loading states
- Built-in error handling
- DevTools for debugging

### 3. **User Experience**

- Better loading states
- Error recovery
- Offline support (with proper configuration)
- Consistent data across components

### 4. **Production Ready**

- Retry logic for network failures
- Error boundaries for graceful failures
- Memory management with garbage collection
- Configurable cache times

## Migration Guide

### Before (Basic Axios)

```typescript
const [accounts, setAccounts] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  const fetchAccounts = async () => {
    try {
      setLoading(true);
      const response = await getConnectedAccounts();
      setAccounts(response.data.accounts);
    } catch (error) {
      toast.error("Failed to load accounts");
    } finally {
      setLoading(false);
    }
  };

  fetchAccounts();
}, []);
```

### After (TanStack Query)

```typescript
const { data: accounts, isLoading, error } = useConnectedAccounts();
```

## Configuration

### Environment Variables

```env
NEXT_PUBLIC_API_URL=https://mobbishly-unbarbarous-roberto.ngrok-free.dev
```

### QueryClient Options

- `staleTime`: How long data stays fresh (1 minute)
- `retry`: Smart retry logic for different error types
- `refetchOnWindowFocus`: Disabled to prevent unnecessary refetches
- `refetchOnReconnect`: Enabled for network recovery

## DevTools

React Query DevTools are included in development mode:

- Query cache inspection
- Mutation tracking
- Performance monitoring
- Cache invalidation tools

## Best Practices

1. **Use custom hooks** for API calls
2. **Structure query keys** consistently
3. **Handle errors** gracefully
4. **Use optimistic updates** for better UX
5. **Invalidate cache** after mutations
6. **Configure retry logic** appropriately
7. **Monitor performance** with DevTools

## Future Enhancements

- [ ] Infinite queries for pagination
- [ ] Offline support with persistence
- [ ] Real-time updates with WebSocket integration
- [ ] Advanced caching strategies
- [ ] Performance monitoring and analytics
