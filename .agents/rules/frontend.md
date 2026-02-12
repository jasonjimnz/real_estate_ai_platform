# Rules for Frontend (TypeScript)

## 1. Build Tooling: Vite is Mandatory

**Rule:** Do not use Create React App (CRA) or Webpack directly. Use **Vite**.

* **Why:** Vite uses native ES modules during development (near-instant start) and Rollup for production builds. It is significantly faster and lighter than Webpack-based tools.
* **Standard:**
```bash
npm create vite@latest my-app -- --template react-ts

```

## 2. Strict Type Safety (No `any`)

**Rule:** The usage of `any` is strictly forbidden. If a type is unknown, use `unknown` and narrow it down, or use Generics.

* **Configuration:** Your `tsconfig.json` must have `"strict": true`.
* **Why:** `any` defeats the purpose of TypeScript and leads to runtime errors that are hard to debug.

```typescript
// ❌ WRONG
const handleData = (data: any) => {
  console.log(data.id); // Might crash if data is null
}

// ✅ CORRECT
interface UserData {
  id: string;
  name: string;
}

const handleData = (data: UserData) => {
  console.log(data.id);
}

```

## 3. State Management: Keep it Local/Atomic

**Rule:** Avoid Redux/Context for everything. Prefer **Zustand** (for global state) or **React Query / TanStack Query** (for server state).

* **Philosophy:** "Server state" (data from API) is not "Global state."
* **Server State:** Use `useQuery` (handles caching, loading, error states automatically).
* **Client State:** Use `useState` (local) or `Zustand` (global UI state like "isSidebarOpen").



```typescript
// ✅ CORRECT (Using TanStack Query for API data)
const { data, isLoading } = useQuery({
  queryKey: ['user', id],
  queryFn: fetchUser
});

// ❌ WRONG (Manually managing API state in Redux/Store)
// dispatch(fetchUserStart());
// try { ... dispatch(fetchUserSuccess(data)) } catch { ... }

```

## 4. CSS Strategy: Vanilla CSS with Variables

**Rule:** Do not use Tailwind, Bootstrap, or Runtime CSS-in-JS (Styled Components). Use **Standard CSS** (or CSS Modules) leveraging modern native features.

* **Structure:** Define global tokens (colors, spacing) in a `:root` variable block.
* **Why:** Modern CSS is powerful enough to not need preprocessors. It keeps the bundle size minimal and the project dependency-free.

```css
/* src/styles/variables.css */
:root {
  --primary-color: #3b82f6;
  --spacing-md: 1rem;
  --font-base: 'Inter', sans-serif;
}

/* Component usage */
.card {
  background: white;
  padding: var(--spacing-md);
  border: 1px solid var(--primary-color);
}

```

## 5. Project Structure: Feature-Based

**Rule:** Do not group files by type (`components/`, `hooks/`, `utils/`). Group by **Feature**.

* **Why:** When you delete a feature (e.g., "UserAuth"), you delete one folder, not files scattered across 5 directories.

```text
src/
  features/
    auth/
      components/
        LoginForm.tsx
      styles/
        LoginForm.css  <-- Co-located vanilla CSS
      hooks/
        useLogin.ts
      types/
        index.ts
    dashboard/
      DashboardLayout.tsx
  ui/ (Shared generic components like Buttons, Inputs)
  lib/ (Axios setup, QueryClient)

```

## 6. Performance: Code Splitting & Lazy Loading

**Rule:** Any route or heavy component (like a Chart or Markdown editor) must be lazy-loaded.

* **Pattern:** Use `React.lazy` and `Suspense`.

```typescript
// router.tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./features/dashboard/Dashboard'));

const AppRoutes = () => (
  <Suspense fallback={<div className="loading-spinner">Loading...</div>}>
    <Routes>
      <Route path="/dashboard" element={<Dashboard />} />
    </Routes>
  </Suspense>
);

```

## 7. API Layer: Typed & Centralized

**Rule:** Do not call `fetch` or `axios` directly inside components. Use a centralized client with interceptors.

* **Why:** Allows global error handling (e.g., "401 Unauthorized" -> redirect to login) in one place.

```typescript
// lib/api.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => Promise.reject(error)
);

// usage
export const getUser = (id: string) => apiClient.get<UserData>(`/users/${id}`);

```

## 8. Env Variables: Type Safe

**Rule:** Access environment variables through a typed configuration object, not `process.env` directly. Vite exposes them on `import.meta.env`.

```typescript
// config.ts
export const config = {
  API_URL: import.meta.env.VITE_API_URL as string,
  IS_DEV: import.meta.env.DEV,
};

// Usage
// import { config } from '@/config';

```