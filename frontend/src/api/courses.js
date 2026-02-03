import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds for sync operations
});

/**
 * Get paginated list of courses with optional filters
 */
export const getCourses = async (filters = {}) => {
  try {
    const params = new URLSearchParams();
    
    if (filters.search) params.append('q', filters.search);
    if (filters.language) params.append('language', filters.language);
    if (filters.level) params.append('level', filters.level);
    if (filters.source) params.append('source', filters.source);
    if (filters.page) params.append('page', filters.page);
    if (filters.per_page) params.append('per_page', filters.per_page);
    
    const response = await api.get(`/courses?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching courses:', error);
    throw error;
  }
};

/**
 * Get course by ID
 */
export const getCourseById = async (id) => {
  const response = await api.get(`/courses/${id}`);
  return response.data;
};

/**
 * Get similar courses for a given course
 */
export const getSimilarCourses = async (courseId, limit = 5) => {
  const response = await api.get(`/courses/${courseId}/similar?limit=${limit}`);
  return response.data;
};

/**
 * Get analytics data
 */
export const getAnalytics = async () => {
  const response = await api.get('/analytics');
  return response.data;
};

/**
 * Get available filter options
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
 * Trigger sync for MIT OpenCourseWare
 */
export const syncMitOcw = async (maxCourses = 50) => {
  const response = await api.post('/sync/mit_ocw', { max_courses: maxCourses });
  return response.data;
};

/**
 * Get sync status
 */
export const getSyncStatus = async (taskId) => {
  const response = await api.get(`/sync/status/${taskId}`);
  return response.data;
};

export default api;