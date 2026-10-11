import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/app-shell';
import { LoginPage } from '@/pages/Login';
import { DashboardPage } from '@/pages/Dashboard';
import { SonarAnalysisPage } from '@/pages/SonarAnalysis';
import { MissionsPage } from '@/pages/Missions';
import { ScansPage } from '@/pages/Scans';
import { DetectionsPage } from '@/pages/Detections';
import { HotspotsPage } from '@/pages/Hotspots';
import { AnalyticsPage } from '@/pages/Analytics';
import { ReviewPage } from '@/pages/Review';
import { ModelsPage } from '@/pages/Models';
import { ReportsPage } from '@/pages/Reports';
import { SettingsPage } from '@/pages/Settings';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<AppShell />}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/sonar-analysis" element={<SonarAnalysisPage />} />
        <Route path="/sonar-analysis/:scanId" element={<SonarAnalysisPage />} />
        <Route path="/missions" element={<MissionsPage />} />
        <Route path="/missions/:missionId" element={<MissionsPage />} />
        <Route path="/scans" element={<ScansPage />} />
        <Route path="/detections" element={<DetectionsPage />} />
        <Route path="/hotspots" element={<HotspotsPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/review" element={<ReviewPage />} />
        <Route path="/models" element={<ModelsPage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Route>
    </Routes>
  );
}