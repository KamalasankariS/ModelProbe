import { Routes, Route, NavLink, Link } from "react-router-dom";
import Landing from "./pages/Landing";
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
      end
      className={({ isActive }) =>
        `px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
          isActive
            ? "bg-amber-100 text-amber-800"
            : "text-stone-500 hover:text-charcoal hover:bg-sand"
        }`
      }
    >
      {label}
    </NavLink>
  );
}

function DashboardLayout() {
  return (
    <div className="min-h-screen bg-cream text-charcoal flex flex-col">
      <header className="border-b border-border bg-white px-6 py-3 flex items-center gap-6 shadow-sm">
        <Link to="/" className="font-bold text-lg tracking-tight text-charcoal hover:text-amber-700 transition-colors">
          ModelProbe
        </Link>
        <nav className="flex gap-1">
          <NavItem to="/dashboard" label="Overview" />
          <NavItem to="/dashboard/suites" label="Suites" />
          <NavItem to="/dashboard/playground" label="Playground" />
        </nav>
      </header>
      <main className="flex-1 p-6 max-w-7xl mx-auto w-full">
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

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/dashboard/*" element={<DashboardLayout />} />
    </Routes>
  );
}
