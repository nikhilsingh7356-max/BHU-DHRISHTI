import { useState, useCallback } from 'react';
import { TopBar } from './components/layout/TopBar';
import { LevelNav } from './components/navigation/LevelNav';
import { WorkflowEngine } from './components/workflow/WorkflowEngine';
import { LoginModal } from './components/auth/LoginModal';
import { ParcelMapSection } from './components/map/ParcelMapSection';
import BottleneckAlerts from './components/alerts/BottleneckAlerts';
import ParcelSummary from './components/common/ParcelSummary';
import { DEMO_PROJECTS } from './data/mockData';
import { logout, hasStoredSession } from './lib/api';
import { ShieldCheck, MapPin, FolderOpen, Activity, Map } from 'lucide-react';

/**
 * BHU-DRISHTI â€” Application Shell
 *
 * Layout:
 *   Desktop:  TopBar â†’ LevelNav â†’ Header â†’ Map (full) â†’ Alerts+Summary â†’ Workflow
 *   Mobile:   TopBar â†’ LevelNav â†’ Header â†’ Map â†’ Summary â†’ Alerts â†’ Workflow
 */
export function App() {
  // â”€â”€ Auth & Navigation â”€â”€
  // Starts unauthenticated. Seeding this with a mock officer made the dashboard
  // render as though a real officer were signed in before any credential was
  // ever checked; the role shown in the TopBar was decorative.
  const [currentUser, setCurrentUser] = useState(null);
  const [currentJurisdiction, setCurrentJurisdiction] = useState({
    stateCode: 'UP',
    stateName: 'Uttar Pradesh',
    district: 'Sitapur',
  });
  const [activeLevel, setActiveLevel] = useState('national');
  // No stored session means nobody has signed in yet, so prompt immediately.
  // Derived as lazy initial state rather than in an effect: opening the dialog
  // is a decision about the first render, not a reaction to it.
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(() => !hasStoredSession());

  // â”€â”€ Project & Workflow â”€â”€
  const [selectedProject, setSelectedProject] = useState(DEMO_PROJECTS[0]);
  const [activeStageId, setActiveStageId] = useState(DEMO_PROJECTS[0].currentStageId);

  // Keep the workflow stage in sync when the project changes, otherwise the
  // engine keeps rendering the previous project's stage.
  const handleProjectSelect = useCallback((project) => {
    if (!project) return;
    setSelectedProject(project);
    setActiveStageId(project.currentStageId);
  }, []);

  // â”€â”€ Parcel State (shared across Map, Alerts, Summary) â”€â”€
  // Only the selected parcel lives here. The parcel collection itself is owned
  // by ParcelMapSection, which defers both the request and the map code until
  // the section approaches the viewport.
  const [selectedParcel, setSelectedParcel] = useState(null);

  const handleStageSelect = useCallback((stageId) => {
    setActiveStageId(stageId);
  }, []);

  // Drop the persisted session token on logout, otherwise a stale bearer token
  // survives logout and is sent with the next request.
  const handleLogout = useCallback(() => {
    logout();
    setCurrentUser(null);
    setIsLoginModalOpen(true);
  }, []);

  const handleLoginSuccess = useCallback((officer) => {
    if (!officer) return;
    setCurrentUser(officer);

    // Narrow the jurisdiction to the officer's own state/district. Only known
    // state names map to a code â€” anything else falls back to national scope.
    const STATE_CODES = { 'Uttar Pradesh': 'UP', Maharashtra: 'MH', Rajasthan: 'RJ' };
    const code = STATE_CODES[officer.state];
    if (code) {
      setCurrentJurisdiction({
        stateCode: code,
        stateName: officer.state,
        district: officer.district || 'All Districts',
      });
    } else {
      setCurrentJurisdiction({
        stateCode: 'ALL',
        stateName: 'All States (National Scope)',
        district: 'All Districts',
      });
    }
  }, []);

  // Primitive deps â€” narrow and stable, so ParcelMapSection's fetch only re-runs
  // when the actual query inputs change (not on every parent render).
  const projectCode = selectedProject?.code;
  const district = currentJurisdiction?.district;

  // Clear the selection when the query inputs change, otherwise a parcel from
  // the previous project can stay highlighted on the new map.
  const queryKey = `${projectCode}|${district}`;
  const [lastQueryKey, setLastQueryKey] = useState(queryKey);
  if (queryKey !== lastQueryKey) {
    setLastQueryKey(queryKey);
    setSelectedParcel(null);
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-gov-text overflow-x-hidden">

      {/* â•â•â•â•â•â•â• TOP BAR â•â•â•â•â•â•â• */}
      <TopBar
        currentUser={currentUser}
        currentJurisdiction={currentJurisdiction}
        onJurisdictionChange={setCurrentJurisdiction}
        onOpenLogin={() => setIsLoginModalOpen(true)}
        onLogout={handleLogout}
      />

      {/* â•â•â•â•â•â•â• LEVEL NAV â•â•â•â•â•â•â• */}
      <LevelNav
        activeLevel={activeLevel}
        onLevelChange={setActiveLevel}
        breadcrumbs={[
          currentJurisdiction.stateCode !== 'ALL' && {
            label: currentJurisdiction.stateName,
          },
          currentJurisdiction.stateCode !== 'ALL' && {
            label: currentJurisdiction.district,
          },
          selectedProject && { label: selectedProject.code },
          selectedProject && { label: 'ULPIN-2026-UP0417-001' },
        ].filter(Boolean)}
      />

      {/* â•â•â•â•â•â•â• MAIN CONTENT â•â•â•â•â•â•â• */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {/* â”€â”€ Page Header â”€â”€ */}
        <div className="space-y-1">
          <h2 className="text-lg sm:text-2xl font-bold text-slate-900 leading-tight">
            Land Acquisition Control Tower
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 max-w-2xl leading-relaxed">
            Monitor statutory workflow, identify emerging delays, and coordinate
            timely intervention.
          </p>
        </div>

        {/* â”€â”€ Project Context (compact banner) â”€â”€ */}
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3 flex flex-wrap items-center gap-3 sm:gap-4 text-xs">
          <div className="flex items-center gap-2 min-w-0">
            <FolderOpen className="w-3.5 h-3.5 text-teal-600 shrink-0" />
            <label htmlFor="project-select" className="sr-only">
              Select project
            </label>
            <select
              id="project-select"
              value={selectedProject.code}
              onChange={(e) => {
                const next = DEMO_PROJECTS.find((p) => p.code === e.target.value);
                if (next) handleProjectSelect(next);
              }}
              className="font-mono font-bold text-teal-700 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded cursor-pointer max-w-[190px] truncate"
              title={selectedProject.title}
            >
              {DEMO_PROJECTS.map((p) => (
                <option key={p.code} value={p.code}>
                  {p.code}
                </option>
              ))}
            </select>
            <span className="text-slate-500 truncate hidden sm:inline">{selectedProject.title}</span>
          </div>
          <div className="flex items-center gap-1 text-slate-400">
            <MapPin className="w-3 h-3" />
            <span>{currentJurisdiction.stateName}</span>
            <span>â€º</span>
            <span>{currentJurisdiction.district}</span>
          </div>
          <span className="flex items-center gap-1 text-xs font-mono font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded ml-auto">
            <Activity className="w-3 h-3" />
            Active
          </span>
        </div>

        {/* â•â•â•â•â•â•â• GIS PARCEL MAP â•â•â•â•â•â•â• */}
        <section aria-label="Parcel map">
          <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
            <div className="bg-slate-50 border-b border-slate-200 px-4 py-2.5 flex items-center gap-2">
              <Map className="w-4 h-4 text-teal-600" />
              <span className="text-xs font-semibold text-slate-700 uppercase tracking-wider">
                GIS Parcel Map
              </span>
            </div>
            <div className="p-0">
              <ParcelMapSection
                projectCode={projectCode}
                district={district}
                selectedParcel={selectedParcel}
                onParcelSelect={setSelectedParcel}
              />
            </div>
          </div>
        </section>

        {/* â•â•â•â•â•â•â• ALERTS + PARCEL SUMMARY â•â•â•â•â•â•â• */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Bottleneck Alerts */}
          <section aria-label="Bottleneck alerts">
            <BottleneckAlerts
              projectCode={selectedProject?.code}
              onParcelSelect={setSelectedParcel}
            />
          </section>

          {/* Selected Parcel Summary */}
          <section aria-label="Selected parcel summary">
            <ParcelSummary selectedParcel={selectedParcel} />
          </section>
        </div>

        {/* â•â•â•â•â•â•â• WORKFLOW ENGINE â•â•â•â•â•â•â• */}
        <section aria-label="Statutory workflow engine">
          <WorkflowEngine
            selectedProject={selectedProject}
            currentStage={activeStageId}
            onStageSelect={handleStageSelect}
            currentUser={currentUser}
          />
        </section>
      </main>

      {/* â•â•â•â•â•â•â• FOOTER â•â•â•â•â•â•â• */}
      <footer className="bg-slate-900 text-slate-400 text-xs border-t border-slate-800 py-5 sm:py-6 mt-auto no-print">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-3 sm:space-y-0 sm:flex sm:flex-wrap sm:items-center sm:justify-between sm:gap-4">
          <div className="space-y-1 min-w-0">
            <div className="font-bold text-white uppercase tracking-wider font-mono text-xs sm:text-xs truncate">
              BHU-DRISHTI â€” SIH 2026 PS 26016
            </div>
            <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
              Dept. of Land Resources (DoLR), Ministry of Rural Development,
              Govt. of India.
            </p>
          </div>
          <div className="flex items-center gap-3 sm:gap-4 text-xs sm:text-sm font-mono flex-wrap">
            <span className="flex items-center gap-1 text-teal-400">
              <ShieldCheck className="w-3.5 h-3.5 shrink-0" />
              RFCTLARR Compliant
            </span>
            <span className="text-slate-600">|</span>
            <span className="text-slate-400">v1.0.0</span>
          </div>
        </div>
      </footer>

      {/* â•â•â•â•â•â•â• LOGIN MODAL â•â•â•â•â•â•â• */}
      <LoginModal
        isOpen={isLoginModalOpen}
        onClose={() => setIsLoginModalOpen(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
}

export default App;
