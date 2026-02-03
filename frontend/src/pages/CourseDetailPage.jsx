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
      setLoading(true);
      setError(null);
      
      try {
        const courseData = await getCourseById(id);
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
        setError('Failed to load course details.');
        console.error('Error fetching course:', err);
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
    if (name.includes('coursera')) return 'coursera';
    if (name.includes('mit') || name.includes('opencourseware')) return 'mit';
    return '';
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

      <span className={`source-badge ${getSourceClass()}`}>
        {getSourceName()}
      </span>

      <div className="course-header">
        <h1>{course.title}</h1>
        <div className="course-meta-badges">
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
          <dd>{course.language || 'Not specified'}</dd>
          
          <dt>Level</dt>
          <dd>{course.level || 'Not specified'}</dd>
          
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
          <SimilarCourses courses={similarCourses} />
        </section>
      )}
    </div>
  );
}

export default CourseDetailPage;