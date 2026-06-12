import React from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar, Legend } from 'recharts';
import { BarChart3, Scan, ShieldAlert, Award, FileSpreadsheet, Eye } from 'lucide-react';
import { getHistory, getAnalyticsStats } from '../utils/history';

const COLORS = ['#4c8d76', '#ba880c', '#3a725e', '#a68c72', '#d7ab10', '#6c5143'];
const HEALTH_COLORS = ['#22c55e', '#ef4444'];

// Mock data to show when user has no scan history yet
const MOCK_STATS = {
  totalScans: 42,
  healthyCount: 18,
  diseasedCount: 24,
  cropDistribution: [
    { name: 'Tomato', value: 15 },
    { name: 'Wheat', value: 12 },
    { name: 'Rice', value: 8 },
    { name: 'Cabbage', value: 7 },
  ],
  diseaseDistribution: [
    { name: 'Tomato - Late Blight', value: 9 },
    { name: 'Wheat - Brown Rust', value: 6 },
    { name: 'Rice - Brown Spot', value: 5 },
    { name: 'Tomato - Leaf Mold', value: 4 },
  ],
  recentActivity: [
    { date: 'Jun 01', scans: 4, diseased: 2, healthy: 2 },
    { date: 'Jun 02', scans: 6, diseased: 4, healthy: 2 },
    { date: 'Jun 03', scans: 5, diseased: 3, healthy: 2 },
    { date: 'Jun 04', scans: 8, diseased: 5, healthy: 3 },
    { date: 'Jun 05', scans: 7, diseased: 3, healthy: 4 },
    { date: 'Jun 06', scans: 12, diseased: 7, healthy: 5 },
  ]
};

export default function AnalyticsDashboard() {
  const history = getHistory();
  const hasHistory = history.length > 0;
  
  // Use real data if available, otherwise fallback to mock data
  const stats = hasHistory ? getAnalyticsStats() : MOCK_STATS;
  const averageConfidence = hasHistory 
    ? Math.round(history.reduce((acc, curr) => acc + curr.confidence, 0) / history.length) 
    : 92;

  const healthData = [
    { name: 'Healthy Crops', value: stats.healthyCount },
    { name: 'Diseased Crops', value: stats.diseasedCount }
  ];

  return (
    <div className="mx-auto max-w-6xl px-4 py-8 space-y-8">
      {/* Top Banner */}
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-primary-600" />
            Analytics Dashboard
          </h2>
          <p className="text-sm text-slate-500">Real-time statistics of crop disease scans, diagnosed pathogens, and model accuracies.</p>
        </div>
        
        {!hasHistory && (
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800 border border-amber-200">
            <Eye className="w-3.5 h-3.5" />
            Viewing Demonstration Data
          </span>
        )}
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Scans Card */}
        <div className="bg-white border border-slate-200 p-5 sm:p-6 rounded-2xl shadow-sm space-y-2">
          <div className="p-2 w-fit bg-primary-50 rounded-xl text-primary-600">
            <Scan className="w-5 h-5" />
          </div>
          <p className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider">Total Scans</p>
          <p className="text-2xl sm:text-3xl font-serif font-black text-slate-900">{stats.totalScans}</p>
        </div>

        {/* Diseased Detected Card */}
        <div className="bg-white border border-slate-200 p-5 sm:p-6 rounded-2xl shadow-sm space-y-2">
          <div className="p-2 w-fit bg-rose-50 rounded-xl text-rose-600">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <p className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider">Diseases Detected</p>
          <p className="text-2xl sm:text-3xl font-serif font-black text-rose-700">{stats.diseasedCount}</p>
        </div>

        {/* Healthy Crops Card */}
        <div className="bg-white border border-slate-200 p-5 sm:p-6 rounded-2xl shadow-sm space-y-2">
          <div className="p-2 w-fit bg-emerald-50 rounded-xl text-emerald-600">
            <Award className="w-5 h-5" />
          </div>
          <p className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider">Healthy Diagnoses</p>
          <p className="text-2xl sm:text-3xl font-serif font-black text-emerald-600">{stats.healthyCount}</p>
        </div>

        {/* Avg Confidence Card */}
        <div className="bg-white border border-slate-200 p-5 sm:p-6 rounded-2xl shadow-sm space-y-2">
          <div className="p-2 w-fit bg-amber-50 rounded-xl text-amber-600">
            <FileSpreadsheet className="w-5 h-5" />
          </div>
          <p className="text-[10px] sm:text-xs text-slate-400 font-bold uppercase tracking-wider">Avg AI Confidence</p>
          <p className="text-2xl sm:text-3xl font-serif font-black text-amber-700">{averageConfidence}%</p>
        </div>
      </div>

      {/* Main Charts Row */}
      <div className="grid lg:grid-cols-3 gap-6">
        {/* Trend Area Chart */}
        <div className="lg:col-span-2 bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4">
          <div>
            <h3 className="font-serif text-lg font-bold text-slate-900">Scanning Trends</h3>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-0.5">Timeline of leaf analyses</p>
          </div>
          
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={stats.recentActivity} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorScans" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4c8d76" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#4c8d76" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorDiseased" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 600 }} stroke="#cbd5e1" />
                <YAxis tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 600 }} stroke="#cbd5e1" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px' }} 
                  labelStyle={{ fontWeight: 'bold', color: '#1e293b' }}
                />
                <Area type="monotone" dataKey="scans" name="Total Scans" stroke="#4c8d76" strokeWidth={2.5} fillOpacity={1} fill="url(#colorScans)" />
                <Area type="monotone" dataKey="diseased" name="Diseased" stroke="#ef4444" strokeWidth={1.5} fillOpacity={1} fill="url(#colorDiseased)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Ratio Pie Chart */}
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm flex flex-col justify-between space-y-4">
          <div>
            <h3 className="font-serif text-lg font-bold text-slate-900">Health Distribution</h3>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-0.5">Healthy vs infected ratio</p>
          </div>

          <div className="h-56 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={healthData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {healthData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={HEALTH_COLORS[index % HEALTH_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px' }}
                />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Center Summary Text */}
            <div className="absolute flex flex-col items-center">
              <span className="text-3xl font-bold font-serif text-slate-800">
                {Math.round((stats.healthyCount / (stats.totalScans || 1)) * 100)}%
              </span>
              <span className="text-[9px] font-bold text-slate-400 uppercase tracking-wide">Healthy Ratio</span>
            </div>
          </div>

          {/* Custom Legends */}
          <div className="flex gap-4 items-center justify-center pt-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-bold">
              <span className="w-3 h-3 rounded-full bg-[#22c55e]"></span>
              Healthy ({stats.healthyCount})
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-bold">
              <span className="w-3 h-3 rounded-full bg-[#ef4444]"></span>
              Diseased ({stats.diseasedCount})
            </div>
          </div>
        </div>
      </div>

      {/* Secondary Charts Row */}
      <div className="grid lg:grid-cols-2 gap-6">
        {/* Crop Distribution Bar Chart */}
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4">
          <div>
            <h3 className="font-serif text-lg font-bold text-slate-900">Scanned Crops</h3>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-0.5">Crop category frequencies</p>
          </div>

          {stats.cropDistribution.length > 0 ? (
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={stats.cropDistribution} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 600 }} stroke="#cbd5e1" />
                  <YAxis tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 600 }} stroke="#cbd5e1" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '12px' }}
                    cursor={{ fill: 'rgba(76, 141, 118, 0.05)' }}
                  />
                  <Bar dataKey="value" name="Scans" radius={[4, 4, 0, 0]}>
                    {stats.cropDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-400 text-sm">
              No crop distribution data.
            </div>
          )}
        </div>

        {/* Top Diagnosed Diseases List */}
        <div className="bg-white border border-slate-200 p-6 rounded-2xl shadow-sm space-y-4">
          <div>
            <h3 className="font-serif text-lg font-bold text-slate-900">Most Detected Diseases</h3>
            <p className="text-xs text-slate-400 font-semibold uppercase mt-0.5">Most common pathogens on your crops</p>
          </div>

          <div className="space-y-4 pt-2">
            {stats.diseaseDistribution.length > 0 ? (
              stats.diseaseDistribution.map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between items-center text-sm font-bold text-slate-700">
                    <span className="flex items-center gap-2">
                      <span className="text-xs font-extrabold text-slate-400 bg-slate-100 w-5 h-5 flex items-center justify-center rounded-full">
                        {idx + 1}
                      </span>
                      {item.name}
                    </span>
                    <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md">
                      {item.value} {item.value === 1 ? 'scan' : 'scans'}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                    <div 
                      className="bg-primary-500 h-full rounded-full" 
                      style={{ width: `${(item.value / stats.totalScans) * 100}%` }}
                    />
                  </div>
                </div>
              ))
            ) : (
              <div className="h-56 flex flex-col items-center justify-center text-slate-400 text-sm text-center">
                <p className="font-semibold text-slate-500">No diseases scanned yet</p>
                <p className="text-xs text-slate-400 max-w-[240px] mt-1">Once you detect a crop disease, it will be mapped here.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
