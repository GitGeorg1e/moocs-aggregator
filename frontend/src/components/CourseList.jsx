import CourseCard from './CourseCard';
import './CourseList.css';

function CourseList({ courses }) {
  if (!courses || courses.length === 0) {
    return (
      <div className="course-list-empty">
        <p>No courses found. Try adjusting your search or filters.</p>
      </div>
    );
  }

  return (
    <div className="courses-grid">
      {courses.map(course => (
        <CourseCard key={course.id} course={course} />
      ))}
    </div>
  );
}

export default CourseList;