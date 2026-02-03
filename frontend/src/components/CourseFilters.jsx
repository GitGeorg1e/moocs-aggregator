function CourseFilters({ filters, onFilterChange, onClearFilters }) {
  const languages = ['English', 'Spanish', 'French', 'German'];
  const levels = ['Beginner', 'Intermediate', 'Advanced'];
  const sources = ['Coursera', 'MIT OpenCourseWare'];

  const handleChange = (filterType, value) => {
    onFilterChange(filterType, value);
  };

  const clearFilters = () => {
    if (onClearFilters) {
      onClearFilters();
    }
  };

  return (
    <div className="course-filters">
      <h3>Filters</h3>
      
      <div className="filter-group">
        <label>Language</label>
        <select
          value={filters.language || ''}
          onChange={(e) => handleChange('language', e.target.value)}
        >
          <option value="">All Languages</option>
          {languages.map(lang => (
            <option key={lang} value={lang}>{lang}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Level</label>
        <select
          value={filters.level || ''}
          onChange={(e) => handleChange('level', e.target.value)}
        >
          <option value="">All Levels</option>
          {levels.map(level => (
            <option key={level} value={level}>{level}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Source</label>
        <select
          value={filters.source || ''}
          onChange={(e) => handleChange('source', e.target.value)}
        >
          <option value="">All Sources</option>
          {sources.map(source => (
            <option key={source} value={source}>{source}</option>
          ))}
        </select>
      </div>

      <button className="clear-filters" onClick={clearFilters}>
        Clear Filters
      </button>
    </div>
  );
}

export default CourseFilters;