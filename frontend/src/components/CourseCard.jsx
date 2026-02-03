import { Link } from 'react-router-dom';
import './CourseCard.css';

function CourseCard({ course }) {
  if (!course) {
    return null;
  }

  const getSourceName = () => {
    if (course.source_name) return course.source_name;
    if (course.source?.name) return course.source.name;
    if (typeof course.source === 'string') return course.source;
    return 'Unknown';
  };

  const getSourceClass = () => {
    const sourceName = getSourceName().toLowerCase();
    if (sourceName.includes('coursera')) return 'coursera';
    if (sourceName.includes('mit') || sourceName.includes('opencourseware')) return 'mit';
    return 'default';
  };

  const truncateText = (text, maxLength) => {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  return (
    <div className="course-card">
      <div className="course-image">
        {course.thumbnail_url ? (
          <img 
            src={course.thumbnail_url} 
            alt={course.title || 'Course'} 
            onError={(e) => {
              e.target.onerror = null;
              e.target.src = 'https://via.placeholder.com/300x160?text=No+Image';
            }}
          />
        ) : (
          <div className="placeholder-image">
            <span>📚</span>
          </div>
        )}
        <span className={`source-badge ${getSourceClass()}`}>
          {getSourceName()}
        </span>
      </div>
      
      <div className="course-content">
        <h3 className="course-title">
          {truncateText(course.title, 60) || 'Untitled Course'}
        </h3>
        
        <p className="course-description">
          {truncateText(course.short_description || course.description, 100) || 'No description available'}
        </p>
        
        {course.instructor && (
          <p className="course-instructor">
            <span className="instructor-label">Offered by</span>
            <span className="instructor-name">{truncateText(course.instructor, 30)}</span>
          </p>
        )}
        
        <div className="course-meta">
          {course.language && (
            <span className="meta-badge language">
              🌐 {course.language}
            </span>
          )}
          {course.level && (
            <span className="meta-badge level">
              📊 {course.level}
            </span>
          )}
        </div>
        
        <Link to={`/course/${course.id}`} className="view-details-btn">
          View Details
        </Link>
      </div>
    </div>
  );
}

export default CourseCard;