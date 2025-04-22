import React, { createContext, useState, useEffect, useContext } from 'react';
import { login, register, getProfile } from '../api/auth';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      fetchUserProfile();
    } else {
      setLoading(false);
    }
  }, []);
  
  const fetchUserProfile = async () => {
    try {
      const userData = await getProfile();
      setCurrentUser(userData);
    } catch (error) {
      logout();
    } finally {
      setLoading(false);
    }
  };
  
  const userLogin = async (email, password) => {
    setLoading(true);
    try {
      const data = await login(email, password);
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
      setCurrentUser(data.user);
      setError(null);
      return data.user;
    } catch (error) {
      setError('Failed to log in. Please check your credentials.');
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const userRegister = async (username, email, password) => {
    setLoading(true);
    try {
      const data = await register(username, email, password);
      localStorage.setItem('accessToken', data.access);
      localStorage.setItem('refreshToken', data.refresh);
      setCurrentUser(data.user);
      setError(null);
      return data.user;
    } catch (error) {
      setError('Failed to register. Please try again.');
      throw error;
    } finally {
      setLoading(false);
    }
  };
  
  const logout = () => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    setCurrentUser(null);
  };
  
  const value = {
    currentUser,
    loading,
    error,
    login: userLogin,
    register: userRegister,
    logout,
  };
  
  return {children};
};