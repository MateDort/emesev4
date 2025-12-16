import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import HomePage from './pages/HomePage';
import StudyPage from './pages/StudyPage';
import NewsPage from './pages/NewsPage';
import MorningPage from './pages/MorningPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/study" element={<StudyPage />} />
        <Route path="/news" element={<NewsPage />} />
        <Route path="/morning" element={<MorningPage />} />
      </Routes>
    </Router>
  );
}

export default App;

