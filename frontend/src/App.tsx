import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import SportDashboard from './components/SportDashboard';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<div className="p-8 text-center text-gray-500">Select a sport from the sidebar to begin</div>} />
          <Route path=":sport/*" element={<SportDashboard />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
