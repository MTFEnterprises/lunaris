import './App.css';
// Change this path if your Dashboard.tsx lives somewhere else (e.g. './components/Dashboard')
import Dashboard from './pages/Dashboard';

// The Dashboard has its own sidebar and navigation, so it is rendered alone,
// without any old Layout / Sidebar wrapper around it.
export default function App() {
  return <Dashboard />;
}
