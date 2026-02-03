import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <Link to="/">📚 MOOCS Aggregator</Link>
      </div>
      <div className="navbar-links">
        <Link to="/">Courses</Link>
        <Link to="/analytics">Analytics</Link>
      </div>
    </nav>
  );
}

export default Navbar;