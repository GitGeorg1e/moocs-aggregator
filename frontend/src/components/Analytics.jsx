import { useState, useEffect } from 'react';
import { getAnalytics } from '../api/courses';

function Analytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await getAnalytics();
        setAnalytics(data);
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return <div className="analytics-loading">Loading analytics...</div>;
  }

  if (!analytics) {
    return <div className="analytics-error">Failed to load analytics.</div>;
  }

  return (
    <div className="analytics">
      {/* Summary Cards */}
      <div className="analytics-summary">
        <div className="stat-card">
          <h3>Total Courses</h3>
          <span className="stat-number">{analytics.totalCourses}</span>
        </div>
        <div className="stat-card">
          <h3>Recently Added</h3>
          <span className="stat-number">{analytics.recentlyAdded}</span>
        </div>
      </div>

      {/* Charts Section */}
      <div className="analytics-charts">
        {/* Courses by Source */}
        <div className="chart-card">
          <h3>Courses by Source</h3>
          <div className="bar-chart">
            {analytics.coursesBySource && Object.entries(analytics.coursesBySource).map(([source, count]) => (
              <div key={source} className="bar-item">
                <span className="bar-label">{source}</span>
                <div className="bar-container">
                  <div 
                    className={`bar ${source.toLowerCase()}`}
                    style={{ width: `${(count / analytics.totalCourses) * 100}%` }}
                  ></div>
                </div>
                <span className="bar-value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Courses by Level */}
        <div className="chart-card">
          <h3>Courses by Level</h3>
          <div className="bar-chart">
            {analytics.coursesByLevel && Object.entries(analytics.coursesByLevel).map(([level, count]) => (
              <div key={level} className="bar-item">
                <span className="bar-label">{level}</span>
                <div className="bar-container">
                  <div 
                    className="bar level-bar"
                    style={{ width: `${(count / analytics.totalCourses) * 100}%` }}
                  ></div>
                </div>
                <span className="bar-value">{count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Courses by Language */}
        <div className="chart-card">
          <h3>Courses by Language</h3>
          <div className="bar-chart">
            {analytics.coursesByLanguage && Object.entries(analytics.coursesByLanguage).map(([lang, count]) => (
              <div key={lang} className="bar-item">
                <span className="bar-label">{lang}</span>
                <div className="bar-container">
                  <div 
                    className="bar language-bar"
                    style={{ width: `${(count / analytics.totalCourses) * 100}%` }}
                  ></div>
                </div>
                <span className="bar-value">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Rated Courses */}
      <div className="top-rated-section">
        <h3>⭐ Top Rated Courses</h3>
        <div className="top-rated-list">
          {analytics.topRatedCourses && analytics.topRatedCourses.map((course, index) => (
            <div key={index} className="top-rated-item">
              <span className="rank">#{index + 1}</span>
              <span className="title">{course.title}</span>
              <span className={`source-badge ${course.source?.toLowerCase() || 'unknown'}`}>
                {course.source || 'Unknown'}
              </span>
              <span className="rating">⭐ {course.rating}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Analytics;