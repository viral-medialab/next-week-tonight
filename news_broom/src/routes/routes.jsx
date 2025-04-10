import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import HomePage from "../pages/HomePage";
import NewProject from "../pages/NewProject";
import GeneratingScenarios from "../pages/GeneratingScenarios";
import KnowledgeGraphPage from "../pages/KnowledgeGraphPage";
import ScenarioAnalysis from "../pages/ScenarioAnalysis";
import NewsStory from "../pages/NewsStory";

const AppRoutes = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="new-project" element={<NewProject />} />
          <Route path="generating-scenarios" element={<GeneratingScenarios />} />
          <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
          <Route path="scenario-analysis" element={<ScenarioAnalysis />} />
          <Route path="finalvedio" element={<NewsStory />} />
        </Route>
      </Routes>
    </Router>
  );
};

export default AppRoutes;