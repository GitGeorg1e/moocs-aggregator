import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getSimilarCourses } from '../api/courses';

function SimilarCourses({ courseId }) {
  const [similarCourses, setSimilarCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSimilar = async () => {
      setLoading(true);
      try {
        const data = await getSimilarCourses(courseId);
        setSimilarCourses(data);
      } catch (error) {
        console.error('Error fetching similar courses:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSimilar();
  }, [courseId]);

  if (loading) {
    return (
      <div className="similar-courses">
        <h3>Similar Courses</h3>
        <p>Loading recommendations...</p>
      </div>
    );
  }

  if (similarCourses.length === 0) {
    return (
      <div className="similar-courses">
        <h3>Similar Courses</h3>
        <p>No similar courses found.</p>
      </div>
    );
  }

  return (
    <div className="similar-courses">
      <h3>🎯 Similar Courses (ML Recommendations)</h3>
      <div className="similar-courses-list">
        {similarCourses.map(course => (
          <div key={course.id} className="similar-course-card">
            <img src={course.image_url} alt={course.title} />
            <div className="similar-course-info">
              <h4>{course.title}</h4>
              <span className={`source-badge ${course.source.toLowerCase()}`}>
                {course.source}
              </span>
              <span className="level-badge">{course.level}</span>
              <div className="similarity-score">
                Match: {(course.similarity_score * 100).toFixed(0)}%
              </div>
            </div>
            <Link to={`/course/${course.id}`} className="btn-view">
              View →
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}

export default SimilarCourses;