import React, { createContext, useContext, useState, useEffect } from 'react';
import { User } from '../types';
import { authApi } from '../api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string, role?: string) => Promise<void>;
  logout: () => void;
  quickLoginDemo: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    const storedToken = localStorage.getItem('hybrid_qml_token');
    const storedUser = localStorage.getItem('hybrid_qml_user');

    if (storedToken && storedUser) {
      try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
      } catch (e) {
        localStorage.removeItem('hybrid_qml_token');
        localStorage.removeItem('hybrid_qml_user');
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      const res = await authApi.login({ username, password });
      setToken(res.access_token);
      setUser(res.user);
      localStorage.setItem('hybrid_qml_token', res.access_token);
      localStorage.setItem('hybrid_qml_user', JSON.stringify(res.user));
    } finally {
      setIsLoading(false);
    }
  };

  const register = async (email: string, password: string, full_name: string, role: string = 'clinician') => {
    setIsLoading(true);
    try {
      await authApi.register({ email, password, full_name, role });
      // Automatically log in after registration
      await login(email, password);
    } finally {
      setIsLoading(false);
    }
  };

  const quickLoginDemo = async () => {
    // Attempts to login as default demo user, or registers demo user first if not exists
    try {
      await login('clinician@hybridqml.org', 'DoctorPass123!');
    } catch (err) {
      try {
        await authApi.register({
          email: 'clinician@hybridqml.org',
          password: 'DoctorPass123!',
          full_name: 'Dr. Jane Smith, MD',
          role: 'clinician',
        });
        await login('clinician@hybridqml.org', 'DoctorPass123!');
      } catch (regErr) {
        // Fallback demo user local session if backend auth service is in setup
        const mockUser: User = {
          id: 'demo-clinician-id',
          email: 'clinician@hybridqml.org',
          full_name: 'Dr. Jane Smith, MD',
          role: 'clinician',
          institution: 'Biomedical Oncology Center',
          is_active: true,
          created_at: new Date().toISOString(),
        };
        setUser(mockUser);
        setToken('demo-jwt-token');
        localStorage.setItem('hybrid_qml_token', 'demo-jwt-token');
        localStorage.setItem('hybrid_qml_user', JSON.stringify(mockUser));
      }
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('hybrid_qml_token');
    localStorage.removeItem('hybrid_qml_user');
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        register,
        logout,
        quickLoginDemo,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
