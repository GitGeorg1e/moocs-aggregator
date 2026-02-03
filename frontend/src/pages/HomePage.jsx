import { useState, useEffect, useCallback } from 'react';
import SearchBar from '../components/SearchBar';
import CourseFilters from '../components/CourseFilters';
import CourseList from '../components/CourseList';
import { getCourses } from '../api/courses';
import './HomePage.css';

function HomePage() {
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    language: null,
    level: null,
    source: null,
    page: 1,
    per_page: 12
  });
  const [pagination, setPagination] = useState({
    total: 0,
    page: 1,
    per_page: 12,
    total_pages: 0
  });

  const fetchCourses = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Build clean filters object (remove null values)
      const cleanFilters = {};
      Object.keys(filters).forEach(key => {
        if (filters[key] !== null && filters[key] !== '') {
          cleanFilters[key] = filters[key];
        }
      });
      
      const response = await getCourses(cleanFilters);
      setCourses(response.data || []);
      setPagination(response.meta || {
        total: 0,
        page: 1,
        per_page: 12,
        total_pages: 0
      });
    } catch (err) {
      setError('Failed to load courses. Please try again later.');
      console.error('Error fetching courses:', err);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchCourses();
  }, [fetchCourses]);

  const handleSearch = (searchTerm) => {
    setFilters(prev => ({ ...prev, search: searchTerm, page: 1 }));
  };

  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({ ...prev, [filterName]: value, page: 1 }));
  };

  const handlePageChange = (newPage) => {
    setFilters(prev => ({ ...prev, page: newPage }));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      language: null,
      level: null,
      source: null,
      page: 1,
      per_page: 12
    });
  };

  return (
    <div className="home-page">
      <div className="search-section">
        <SearchBar onSearch={handleSearch} initialValue={filters.search} />
        <p className="results-count">{pagination.total} courses found</p>
      </div>

      <div className="content-section">
        <aside className="filters-sidebar">
          <CourseFilters
            filters={filters}
            onFilterChange={handleFilterChange}
            onClearFilters={clearFilters}
          />
        </aside>

        <main className="courses-main">
          {error && (
            <div className="error-message">
              <p>{error}</p>
              <button type="button" onClick={fetchCourses}>Retry</button>
            </div>
          )}

          {loading ? (
            <div className="loading-spinner">
              <div className="spinner"></div>
              <p>Loading courses...</p>
            </div>
          ) : (
            <>
              <CourseList courses={courses} />

              {pagination.total_pages > 1 && (
                <div className="pagination">
                  <button
                    type="button"
                    onClick={() => handlePageChange(pagination.page - 1)}
                    disabled={pagination.page <= 1}
                  >
                    Previous
                  </button>
                  <span className="page-info">
                    Page {pagination.page} of {pagination.total_pages}
                  </span>
                  <button
                    type="button"
                    onClick={() => handlePageChange(pagination.page + 1)}
                    disabled={pagination.page >= pagination.total_pages}
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}

export default HomePage;