import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

/**
 * Get paginated list of courses with optional filters
 */
export const getCourses = async (filters = {}) => {
  const params = new URLSearchParams();
  
  if (filters.search && filters.search.trim() !== '') {
    params.append('search', filters.search);
  }
  if (filters.language && filters.language !== '') {
    params.append('language', filters.language);
  }
  if (filters.level && filters.level !== '') {
    params.append('level', filters.level);
  }
  if (filters.source && filters.source !== '') {
    params.append('source', filters.source);
  }
  if (filters.topic && filters.topic !== '') {
    params.append('topic', filters.topic);
  }
  if (filters.page) {
    params.append('page', filters.page);
  }
  if (filters.per_page) {
    params.append('per_page', filters.per_page);
  }
  
  const queryString = params.toString();
  const url = queryString ? `/courses?${queryString}` : '/courses';
  
  const response = await api.get(url);
  return response.data;
};

/**
 * Get course by ID
 */
export const getCourseById = async (id) => {
  console.log('API: Fetching course by ID:', id);
  const response = await api.get(`/courses/${id}`);
  console.log('API: Response:', response.data);
  return response.data;
};

/**
 * Get similar courses for a given course
 */
export const getSimilarCourses = async (courseId, limit = 5) => {
  try {
    const response = await api.get(`/courses/${courseId}/similar?limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching similar courses:', error);
    return [];
  }
};

/**
 * Get analytics data
 */
export const getAnalytics = async () => {
  const response = await api.get('/analytics');
  return response.data;
};

/**
 * Get available filter options from database
 */
export const getFilterOptions = async () => {
  const response = await api.get('/courses/filters');
  return response.data;
};

/**
 * Trigger sync for Coursera
 */
export const syncCoursera = async (maxCourses = 50) => {
  const response = await api.post('/sync/coursera', { max_courses: maxCourses });
  return response.data;
};

/**
 * Get sync status
 */
export const getSyncStatus = async (taskId) => {
  const response = await api.get(`/sync/status/${taskId}`);
  return response.data;
};

/**
 * Get keywords from courses
 */
export const getKeywords = async () => {
  const response = await api.get('/courses/keywords');
  return response.data;
};

export default api;