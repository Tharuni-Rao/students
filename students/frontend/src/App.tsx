import { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BellRing,
  BookOpen,
  Briefcase,
  Download,
  FileUp,
  Filter,
  GraduationCap,
  LogIn,
  ShieldAlert,
  TrendingUp,
  UserCircle2,
  Users,
} from 'lucide-react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';
const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444'];

type RoleKey = 'admin' | 'faculty' | 'placement' | 'student';

type Student = {
  student_id: string;
  name: string;
  department: string;
  degree: string;
  year: number;
  semester: number;
  cgpa: number;
  attendance: number;
  internal_assessment: number;
  success_score: number;
  academic_risk: string;
  placement_risk: string;
  data_completeness: number;
  segments: string[];
  interventions: Array<{ title: string; role: string; priority: string; status: string; description: string }>;
  academic_triggers: string[];
  placement_triggers: string[];
  components: {
    academic: number;
    attendance: number;
    lms: number;
    skills: number;
    placement: number;
    engagement: number;
  };
  aptitude: number;
  coding: number;
  mock_interview: number;
  resume_readiness: number;
  communication_assessment: number;
  assignment_completion: number;
};

type DashboardPayload = {
  kpis: Record<string, number>;
  score_distribution: Array<{ name: string; value: number }>;
  risk_distribution: Array<{ name: string; value: number }>;
  department_performance: Array<{ department: string; avgScore: number; students: number }>;
  attendance_vs_academic: Array<{ attendance: number; academic: number; name: string }>;
  lms_vs_academic: Array<{ lms: number; academic: number; name: string }>;
  semester_trend: Array<{ semester: string; score: number }>;
  placement_by_department: Array<{ department: string; avgPlacement: number }>;
  intervention_status: Array<{ name: string; value: number }>;
  student_list: Student[];
};

const initialFilters = {
  department: 'All',
  year: 'All',
  semester: 'All',
  segment: 'All',
  academic_risk: 'All',
  placement_risk: 'All',
  score_min: '',
  score_max: '',
};

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

function App() {
  const [role, setRole] = useState<RoleKey>('admin');
  const [password, setPassword] = useState('admin123');
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [selectedStudent, setSelectedStudent] = useState<Student | null>(null);
  const [filters, setFilters] = useState(initialFilters);
  const [scenario, setScenario] = useState({ attendance: 78, internal_assessment: 72, coding: 70, aptitude: 68, assignment_completion: 76 });
  const [uploadSummary, setUploadSummary] = useState<string>('');
  const [importResult, setImportResult] = useState<string>('');

  const departments = useMemo(
    () => Array.from(new Set((dashboard?.department_performance ?? []).map((item) => item.department))),
    [dashboard],
  );

  const studentSegments = useMemo(
    () => Array.from(new Set((dashboard?.student_list ?? []).flatMap((student) => student.segments))),
    [dashboard],
  );

  useEffect(() => {
    if (!isAuthenticated) return;
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value && value !== 'All') params.append(key, String(value));
    });
    fetchJson<DashboardPayload>(`${API_BASE}/dashboard?${params.toString()}`)
      .then((data) => {
        setDashboard(data);
        if (data.student_list.length > 0) {
          setSelectedStudent((current) => current ?? data.student_list[0]);
        }
      })
      .catch((error) => console.error('Failed to load dashboard', error));
  }, [filters, isAuthenticated]);

  const handleLogin = async () => {
    try {
      const result = await fetchJson<{ token: string; user: { role: string; name: string; id: string } }>(`${API_BASE}/login`, {
        method: 'POST',
        body: JSON.stringify({ role, password }),
      });
      if (result.token) {
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('Login failed', error);
      setIsAuthenticated(false);
      alert('Demo login failed. Use the provided role password.');
    }
  };

  const handleStudentSelect = async (studentId: string) => {
    try {
      const student = await fetchJson<Student>(`${API_BASE}/students/${studentId}`);
      setSelectedStudent(student);
    } catch (error) {
      console.error('Student fetch failed', error);
    }
  };

  const handleScenarioSubmit = async () => {
    if (!selectedStudent) return;
    try {
      const result = await fetchJson<{ current_score: number; simulated_score: number; difference: number; changes: any; risk: any; explanation: string }>(`${API_BASE}/scenario`, {
        method: 'POST',
        body: JSON.stringify({
          student_id: selectedStudent.student_id,
          changes: {
            attendance: scenario.attendance,
            internal_assessment: scenario.internal_assessment,
            coding: scenario.coding,
            aptitude: scenario.aptitude,
            assignment_completion: scenario.assignment_completion,
          },
        }),
      });
      setUploadSummary(result.explanation + ` Current ${result.current_score} → Simulated ${result.simulated_score} (${result.difference >= 0 ? '+' : ''}${result.difference}).`);
    } catch (error) {
      console.error('Scenario failed', error);
    }
  };

  const handleImport = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append('file', file);
    try {
      const result = await fetch(`${API_BASE}/import`, {
        method: 'POST',
        body: form,
      });
      const data = await result.json();
      setImportResult(`Valid ${data.valid_records} | Rejected ${data.invalid_rows}`);
      setUploadSummary(data.summary ?? 'Import processed.');
      if (data.valid_records > 0) {
        setFilters({ ...initialFilters });
      }
    } catch (error) {
      console.error('Import failed', error);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="login-shell">
        <div className="login-card">
          <div className="brand-row">
            <GraduationCap size={48} />
            <div>
              <p className="eyebrow">Predict. Support. Empower.</p>
              <h1>EduPulse AI</h1>
            </div>
          </div>
          <p className="subtitle">Smart Campus Analytics & Student Success Platform</p>
          <div className="role-grid">
            {(['admin', 'faculty', 'placement', 'student'] as RoleKey[]).map((option) => (
              <button
                key={option}
                className={`role-button ${role === option ? 'selected' : ''}`}
                onClick={() => setRole(option)}
              >
                <span>{option.toUpperCase()}</span>
                {option === 'admin' && 'Administrator'}
                {option === 'faculty' && 'Faculty'}
                {option === 'placement' && 'Placement Officer'}
                {option === 'student' && 'Student'}
              </button>
            ))}
          </div>
          <label className="field-label">Demo password</label>
          <input
            className="text-input"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <button className="primary-button" onClick={handleLogin}>
            <LogIn size={18} /> Continue as {role}
          </button>
          <p className="prototype-note">Prototype demo access only. Real deployments require secure authentication and role authorization.</p>
        </div>
      </div>
    );
  }

  if (!dashboard) {
    return <div className="page-loading">Loading dashboard…</div>;
  }

  const kpis = [
    { label: 'Total students', value: dashboard.kpis.total_students ?? 0, icon: Users },
    { label: 'Average Success Score', value: `${dashboard.kpis.average_score ?? 0}`, icon: TrendingUp },
    { label: 'Academic risk', value: dashboard.kpis.high_academic_risk ?? 0, icon: ShieldAlert },
    { label: 'Placement concerns', value: dashboard.kpis.placement_concerns ?? 0, icon: Briefcase },
    { label: 'Average attendance', value: `${dashboard.kpis.average_attendance ?? 0}%`, icon: Activity },
    { label: 'Incomplete data', value: dashboard.kpis.incomplete_data ?? 0, icon: FileUp },
    { label: 'Open interventions', value: dashboard.kpis.open_interventions ?? 0, icon: BellRing },
  ];

  return (
    <div className="page-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">EduPulse AI</p>
          <h2>Predict. Support. Empower.</h2>
        </div>
        <div className="header-actions">
          <span className="badge">Role: {role}</span>
          <button className="secondary-button" onClick={() => setIsAuthenticated(false)}>Switch role</button>
        </div>
      </header>

      <section className="filters-panel">
        <div className="filter-header">
          <Filter size={18} />
          <span>Filters</span>
        </div>
        <div className="filter-grid">
          <select value={filters.department} onChange={(e) => setFilters({ ...filters, department: e.target.value })}>
            <option value="All">All departments</option>
            {departments.map((dept) => (
              <option key={dept} value={dept}>{dept}</option>
            ))}
          </select>
          <select value={filters.year} onChange={(e) => setFilters({ ...filters, year: e.target.value })}>
            <option value="All">All years</option>
            {[1, 2, 3, 4].map((year) => (
              <option key={year} value={String(year)}>{year}</option>
            ))}
          </select>
          <select value={filters.semester} onChange={(e) => setFilters({ ...filters, semester: e.target.value })}>
            <option value="All">All semesters</option>
            {[1, 2, 3, 4, 5, 6, 7, 8].map((sem) => (
              <option key={sem} value={String(sem)}>{sem}</option>
            ))}
          </select>
          <select value={filters.segment} onChange={(e) => setFilters({ ...filters, segment: e.target.value })}>
            <option value="All">All segments</option>
            {studentSegments.map((segment) => (
              <option key={segment} value={segment}>{segment}</option>
            ))}
          </select>
          <select value={filters.academic_risk} onChange={(e) => setFilters({ ...filters, academic_risk: e.target.value })}>
            <option value="All">All academic risk</option>
            {['Low', 'Moderate', 'High'].map((risk) => (
              <option key={risk} value={risk}>{risk}</option>
            ))}
          </select>
          <select value={filters.placement_risk} onChange={(e) => setFilters({ ...filters, placement_risk: e.target.value })}>
            <option value="All">All placement risk</option>
            {['Low', 'Moderate', 'High'].map((risk) => (
              <option key={risk} value={risk}>{risk}</option>
            ))}
          </select>
          <input
            className="text-input"
            placeholder="Min score"
            value={filters.score_min}
            onChange={(e) => setFilters({ ...filters, score_min: e.target.value })}
          />
          <input
            className="text-input"
            placeholder="Max score"
            value={filters.score_max}
            onChange={(e) => setFilters({ ...filters, score_max: e.target.value })}
          />
        </div>
      </section>

      <section className="metrics-grid">
        {kpis.map(({ label, value, icon: Icon }) => (
          <div key={label} className="metric-card">
            <div className="metric-icon">
              <Icon size={18} />
            </div>
            <div>
              <p>{label}</p>
              <strong>{value}</strong>
            </div>
          </div>
        ))}
      </section>

      <section className="chart-grid">
        <div className="panel">
          <h3>Student Success Score distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dashboard.score_distribution}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h3>Academic risk distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={dashboard.risk_distribution} dataKey="value" nameKey="name" outerRadius={80} innerRadius={40} paddingAngle={3}>
                {dashboard.risk_distribution.map((entry, index) => (
                  <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className="panel wide-panel">
          <h3>Department performance</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={dashboard.department_performance}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="department" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avgScore" fill="#14b8a6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h3>Attendance vs academic</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={dashboard.attendance_vs_academic}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="attendance" stroke="#2563eb" strokeWidth={2} />
              <Line type="monotone" dataKey="academic" stroke="#f59e0b" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel">
          <h3>LMS engagement vs academic</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={dashboard.lms_vs_academic}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" hide />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="lms" stroke="#10b981" strokeWidth={2} />
              <Line type="monotone" dataKey="academic" stroke="#8b5cf6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="panel wide-panel">
          <h3>Semester trend</h3>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={dashboard.semester_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="semester" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="score" stroke="#0f766e" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="content-grid">
        <div className="panel student-panel">
          <div className="panel-header">
            <h3>Student roster</h3>
            <button className="secondary-button small-btn">Export CSV</button>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Student</th>
                  <th>Dept</th>
                  <th>Score</th>
                  <th>Academic</th>
                  <th>Placement</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.student_list.map((student) => (
                  <tr key={student.student_id} onClick={() => handleStudentSelect(student.student_id)} className="clickable-row">
                    <td>{student.name}</td>
                    <td>{student.department}</td>
                    <td>{student.success_score}</td>
                    <td>{student.academic_risk}</td>
                    <td>{student.placement_risk}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="panel side-panel">
          {selectedStudent ? (
            <>
              <div className="student-header">
                <div className="avatar"><UserCircle2 size={36} /></div>
                <div>
                  <h3>{selectedStudent.name}</h3>
                  <p>{selectedStudent.student_id} • {selectedStudent.department}</p>
                </div>
              </div>
              <div className="score-badge">Success Score: {selectedStudent.success_score}</div>
              <div className="mini-grid">
                <div><span>CGPA</span><strong>{selectedStudent.cgpa}</strong></div>
                <div><span>Attendance</span><strong>{selectedStudent.attendance}%</strong></div>
                <div><span>Internal</span><strong>{selectedStudent.internal_assessment}%</strong></div>
                <div><span>Completeness</span><strong>{selectedStudent.data_completeness}%</strong></div>
              </div>
              <div className="risk-block">
                <h4>Academic risk</h4>
                <p>{selectedStudent.academic_risk}</p>
                <ul>
                  {selectedStudent.academic_triggers.length > 0 ? selectedStudent.academic_triggers.map((trigger) => <li key={trigger}>{trigger}</li>) : <li>No major academic warnings.</li>}
                </ul>
              </div>
              <div className="risk-block">
                <h4>Placement risk</h4>
                <p>{selectedStudent.placement_risk}</p>
                <ul>
                  {selectedStudent.placement_triggers.length > 0 ? selectedStudent.placement_triggers.map((trigger) => <li key={trigger}>{trigger}</li>) : <li>No major placement concerns.</li>}
                </ul>
              </div>
              <div className="risk-block">
                <h4>Interventions</h4>
                {selectedStudent.interventions.map((item) => (
                  <div key={item.title} className="intervention-item">
                    <strong>{item.title}</strong>
                    <span>{item.role} • {item.priority} • {item.status}</span>
                    <p>{item.description}</p>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p>No student selected</p>
          )}
        </div>
      </section>

      <section className="bottom-grid">
        <div className="panel sim-panel">
          <h3>Scenario simulator</h3>
          <div className="sim-form">
            <label>Attendance<input type="number" value={scenario.attendance} onChange={(e) => setScenario({ ...scenario, attendance: Number(e.target.value) })} /></label>
            <label>Internal assessment<input type="number" value={scenario.internal_assessment} onChange={(e) => setScenario({ ...scenario, internal_assessment: Number(e.target.value) })} /></label>
            <label>Coding<input type="number" value={scenario.coding} onChange={(e) => setScenario({ ...scenario, coding: Number(e.target.value) })} /></label>
            <label>Aptitude<input type="number" value={scenario.aptitude} onChange={(e) => setScenario({ ...scenario, aptitude: Number(e.target.value) })} /></label>
            <label>Assignment completion<input type="number" value={scenario.assignment_completion} onChange={(e) => setScenario({ ...scenario, assignment_completion: Number(e.target.value) })} /></label>
          </div>
          <button className="primary-button" onClick={handleScenarioSubmit}>Run what-if simulation</button>
          {uploadSummary && <p className="summary-text">{uploadSummary}</p>}
        </div>

        <div className="panel import-panel">
          <h3>Data import</h3>
          <label className="upload-zone">
            <FileUp size={20} />
            <input type="file" accept=".csv,.json" onChange={handleImport} />
          </label>
          <p className="mini-copy">CSV and JSON uploads are validated, summarized, and previewed before integration.</p>
          {importResult && <p className="summary-text">{importResult}</p>}
        </div>
      </section>
    </div>
  );
}

export default App;
