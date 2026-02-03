import { useState, useEffect } from 'react';
import { getFilterOptions } from '../api/courses';
import './CourseFilters.css';

// Map language codes to readable names
const LANGUAGE_LABELS = {
  'en': 'English',
  'zh': 'Chinese (中文)',
  'es': 'Spanish',
  'fr': 'French',
  'de': 'German',
  'ar': 'Arabic',
  'pt': 'Portuguese',
  'ja': 'Japanese',
  'ko': 'Korean',
  'ru': 'Russian'
};

function CourseFilters({ filters, onFilterChange, onClearFilters }) {
  const [options, setOptions] = useState({
    languages: [],
    levels: [],
    sources: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOptions = async () => {
      try {
        const data = await getFilterOptions();
        setOptions({
          languages: data.languages || ['en', 'zh'],
          levels: data.levels || ['Beginner', 'Intermediate', 'Advanced', 'Mixed'],
          sources: data.sources || ['Coursera']
        });
      } catch (error) {
        console.error('Error fetching filter options:', error);
        setOptions({
          languages: ['en', 'zh'],
          levels: ['Beginner', 'Intermediate', 'Advanced', 'Mixed'],
          sources: ['Coursera']
        });
      } finally {
        setLoading(false);
      }
    };
    fetchOptions();
  }, []);

  const handleFilterChange = (filterName, value) => {
    onFilterChange(filterName, value === '' ? null : value);
  };

  const getLanguageLabel = (code) => {
    return LANGUAGE_LABELS[code] || code;
  };

  const hasActiveFilters = filters.language || filters.level || filters.source;

  return (
    <div className="course-filters">
      <div className="filters-header">
        <h3>
          <span className="filter-icon">|</span> Filters
        </h3>
      </div>

      <div className="filter-group">
        <label htmlFor="language">LANGUAGE</label>
        <select
          id="language"
          value={filters.language || ''}
          onChange={(e) => handleFilterChange('language', e.target.value)}
          disabled={loading}
        >
          <option value="">All Languages</option>
          {options.languages.map((lang) => (
            <option key={lang} value={lang}>
              {getLanguageLabel(lang)}
            </option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="level">LEVEL</label>
        <select
          id="level"
          value={filters.level || ''}
          onChange={(e) => handleFilterChange('level', e.target.value)}
          disabled={loading}
        >
          <option value="">All Levels</option>
          {options.levels.map((level) => (
            <option key={level} value={level}>{level}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label htmlFor="source">SOURCE</label>
        <select
          id="source"
          value={filters.source || ''}
          onChange={(e) => handleFilterChange('source', e.target.value)}
          disabled={loading}
        >
          <option value="">All Sources</option>
          {options.sources.map((source) => (
            <option key={source} value={source}>{source}</option>
          ))}
        </select>
      </div>

      {hasActiveFilters && (
        <button 
          type="button"
          className="clear-filters-btn" 
          onClick={onClearFilters}
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}

export default CourseFilters;