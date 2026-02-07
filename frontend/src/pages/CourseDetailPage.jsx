import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getCourseById, getSimilarCourses } from '../api/courses';
import './CourseDetailPage.css';

function CourseDetailPage() {
  const { id } = useParams();
  const [course, setCourse] = useState(null);
  const [similarCourses, setSimilarCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCourseData = async () => {
      if (!id) {
        setError('Invalid course ID');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      
      try {
        console.log('Fetching course with ID:', id);
        const courseData = await getCourseById(id);
        console.log('Course data received:', courseData);
        setCourse(courseData);
        
        // Fetch similar courses
        try {
          const similar = await getSimilarCourses(id, 5);
          setSimilarCourses(similar || []);
        } catch (err) {
          console.log('No similar courses found');
          setSimilarCourses([]);
        }
      } catch (err) {
        console.error('Error fetching course:', err);
        setError('Failed to load course details.');
      } finally {
        setLoading(false);
      }
    };

    fetchCourseData();
  }, [id]);

  const getSourceName = () => {
    if (course?.source_name) return course.source_name;
    if (course?.source?.name) return course.source.name;
    return 'Unknown';
  };

  const getSourceClass = () => {
    const name = getSourceName().toLowerCase();
    if (name.includes('udemy')) return 'udemy';
    return '';
  };

  const getLanguageLabel = (code) => {
    const labels = {
      'en': 'English',
      'zh': 'Chinese',
      'es': 'Spanish',
      'fr': 'French',
      'de': 'German'
    };
    return labels[code] || code;
  };

  if (loading) {
    return (
      <div className="course-detail-page loading">
        <div className="spinner"></div>
        <p>Loading course details...</p>
      </div>
    );
  }

  if (error || !course) {
    return (
      <div className="course-detail-page error">
        <h2>Course Not Found</h2>
        <p>{error || 'The requested course could not be found.'}</p>
        <Link to="/" className="back-link">← Back to Courses</Link>
      </div>
    );
  }

  return (
    <div className="course-detail-page">
      <div className="breadcrumb">
        <Link to="/">Courses</Link> / {course.title}
      </div>

      <span className={`source-badge-top ${getSourceClass()}`}>
        {getSourceName()}
      </span>

      <div className="course-header">
        <h1>{course.title}</h1>
        <div className="course-meta-badges">
          {course.language && (
            <span className="meta-badge language">
              🌐 {getLanguageLabel(course.language)}
            </span>
          )}
          {course.level && (
            <span className="meta-badge level">
              📊 {course.level}
            </span>
          )}
        </div>
      </div>

      <div className="description-section">
        <h2>About this Course</h2>
        <p>{course.full_description || course.short_description || 'No description available.'}</p>
      </div>

      <div className="action-buttons">
        {course.course_url && (
          <a 
            href={course.course_url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn-primary"
          >
            View on {getSourceName()}
          </a>
        )}
      </div>

      <div className="course-info-card">
        <h3>Course Information</h3>
        <dl>
          <dt>Source</dt>
          <dd>{getSourceName()}</dd>
          
          <dt>Language</dt>
          <dd>{getLanguageLabel(course.language) || 'Not specified'}</dd>
          
          <dt>Level</dt>
          <dd>{course.level || 'Not specified'}</dd>

          {course.cluster_id !== null && course.cluster_id !== undefined && (
            <>
              <dt>Cluster</dt>
              <dd>Cluster #{course.cluster_id}</dd>
            </>
          )}
          
          {course.instructor && (
            <>
              <dt>Instructor</dt>
              <dd>{course.instructor}</dd>
            </>
          )}
        </dl>
      </div>

      {similarCourses.length > 0 && (
        <section className="similar-courses-section">
          <h2>Similar Courses</h2>
          <div className="similar-courses-grid">
            {similarCourses.map((c) => (
              <Link key={c.id} to={`/course/${c.id}`} className="similar-course-card">
                <h4>{c.title}</h4>
                <p>{c.short_description?.substring(0, 100)}...</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

export default CourseDetailPage;