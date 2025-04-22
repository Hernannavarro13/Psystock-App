// stock-predictor-frontend/src/contexts/AuthContext.js
import React, { createContext, useState, useEffect, useContext } from 'react';
import { authService } from '../services/api';

// Create context
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Check if user is already logged in
    const user = authService.getCurrentUser();
    setCurrentUser(user);
    setLoading(false);
  }, []);

  // Login function
  const login = async (email, password) => {
    try {
      setLoading(true);
      setError(null);
      const user = await authService.login(email, password);
      setCurrentUser(user);
      return user;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Login failed. Please check your credentials.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Register function
  const register = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      const user = await authService.register(userData);
      setCurrentUser(user);
      return user;
    } catch (err) {
      const errorMessage = err.response?.data?.email?.[0] || 
                          err.response?.data?.username?.[0] || 
                          err.response?.data?.detail || 
                          'Registration failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Logout function
  const logout = () => {
    authService.logout();
    setCurrentUser(null);
  };

  // Update profile function
  const updateProfile = async (userData) => {
    try {
      setLoading(true);
      setError(null);
      const updatedUser = await authService.updateProfile(userData);
      setCurrentUser(updatedUser);
      return updatedUser;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Profile update failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Password reset request
  const resetPasswordRequest = async (email) => {
    try {
      setLoading(true);
      setError(null);
      await authService.resetPasswordRequest(email);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Password reset request failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // Password reset confirm
  const resetPasswordConfirm = async (uid, token, password) => {
    try {
      setLoading(true);
      setError(null);
      await authService.resetPasswordConfirm(uid, token, password);
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Password reset failed. Please try again.';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const value = {
    currentUser,
    loading,
    error,
    login,
    register,
    logout,
    updateProfile,
    resetPasswordRequest,
    resetPasswordConfirm,
    isAuthenticated: authService.isAuthenticated,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// Create hook for using the auth context
export const useAuth = () => {
  return useContext(AuthContext);
};