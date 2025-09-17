'use client';

import { AuthProvider as CustomAuthProvider } from '@/contexts/AuthContext';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <CustomAuthProvider>
      {children}
    </CustomAuthProvider>
  );
}
