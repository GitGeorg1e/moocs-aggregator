import { useState, useEffect } from 'react';
import Analytics from '../components/Analytics';
import { getAnalytics } from '../api/courses';
import '../pages/AnalyticsPage.css';

function AnalyticsPage() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await getAnalytics();
        setAnalytics(data);
      } catch (err) {
        setError('Failed to load analytics data.');
        console.error('Error fetching analytics:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="analytics-page loading">
        <div className="spinner"></div>
        <p>Loading analytics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-page error">
        <h2>Error Loading Analytics</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <div className="analytics-page">
      <header className="page-header">
        <h1>📊 Platform Analytics</h1>
        <p>Insights and statistics from our course catalog</p>
      </header>

      <Analytics data={analytics} />
    </div>
  );
}

export default AnalyticsPage;