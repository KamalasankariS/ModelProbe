import { Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview";
import SuiteList from "./pages/SuiteList";
import SuiteDetail from "./pages/SuiteDetail";
import CompareView from "./pages/CompareView";
import RunDetail from "./pages/RunDetail";
import Playground from "./pages/Playground";

function NavItem({ to, label }: { to: string; label: string }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `px-3 py-2 rounded text-sm font-medium transition-colors ${
          isActive ? "bg-accent text-white" : "text-muted hover:text-white"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

export default function App() {
  return (
    <div className="min-h-screen bg-surface text-white flex flex-col">
      <header className="border-b border-border px-6 py-3 flex items-center gap-6">
        <span className="font-bold text-lg tracking-tight">ModelProbe</span>
        <nav className="flex gap-2">
          <NavItem to="/" label="Overview" />
          <NavItem to="/suites" label="Suites" />
          <NavItem to="/playground" label="Playground" />
        </nav>
      </header>
      <main className="flex-1 p-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/suites" element={<SuiteList />} />
          <Route path="/suites/:name" element={<SuiteDetail />} />
          <Route path="/compare/:name" element={<CompareView />} />
          <Route path="/runs/:id" element={<RunDetail />} />
          <Route path="/playground" element={<Playground />} />
        </Routes>
      </main>
    </div>
  );
}
