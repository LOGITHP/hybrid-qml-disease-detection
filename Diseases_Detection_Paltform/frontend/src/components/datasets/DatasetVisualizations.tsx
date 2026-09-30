import React, { useMemo } from 'react';
import { ResponsiveContainer, BarChart, CartesianGrid, XAxis, YAxis, Tooltip, Bar, PieChart, Pie, Cell } from 'recharts';
import { DatasetAnalysis } from '../../types';

interface DatasetVisualizationsProps {
  analysis: DatasetAnalysis;
}

export const DatasetVisualizations: React.FC<DatasetVisualizationsProps> = ({ analysis }) => {
  const { target_column, class_distribution, column_profiles, columns, missing_value_counts } = analysis;

  const targetData = useMemo(() => {
    if (!class_distribution) return [];
    return Object.entries(class_distribution).map(([name, value]) => ({ name: String(name), value }));
  }, [class_distribution]);

  const missingData = useMemo(() => {
    if (!missing_value_counts) return [];
    const rowCount = analysis.row_count || 1;
    return Object.entries(missing_value_counts)
      .filter(([_, count]) => count > 0)
      .map(([name, count]) => ({
        name,
        count,
        percent: ((count / rowCount) * 100).toFixed(1)
      }))
      .sort((a, b) => b.count - a.count);
  }, [missing_value_counts, analysis.row_count]);

  const COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Target Distribution */}
        <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Target Distribution ({target_column || 'Unknown'})</h3>
          {targetData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={targetData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  >
                    {targetData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic">No target class distribution available.</p>
          )}
        </div>

        {/* Missing Values */}
        {missingData.length > 0 && (
          <div className="card-scientific bg-white border border-slate-200 rounded-xl p-5 shadow-sm space-y-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Missing Values per Feature (%)</h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={missingData} layout="vertical" margin={{ top: 0, right: 20, left: 40, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e2e8f0" />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
                  <YAxis dataKey="name" type="category" tick={{ fontSize: 10 }} />
                  <Tooltip cursor={{ fill: '#f1f5f9' }} formatter={(val: number) => `${val}%`} />
                  <Bar dataKey="percent" fill="#f59e0b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Feature Distributions */}
      <h3 className="text-sm font-bold text-slate-800 border-b border-slate-200 pb-2 mt-8">Feature Distributions</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {columns.map(col => {
          const profile = column_profiles?.[col];
          if (!profile?.distribution?.length || col === target_column) return null;
          
          // Limit to max 15 bars
          const isNumeric = profile.dtype.includes('float') || profile.dtype.includes('int');
          const data = profile.distribution.slice(0, 15).map(item => ({
            name: item.value !== undefined ? String(item.value) : `${item.lower?.toFixed(1)}-${item.upper?.toFixed(1)}`,
            count: item.count
          }));

          return (
            <div key={col} className="card-scientific bg-white border border-slate-200 rounded-xl p-4 shadow-sm space-y-3">
              <h4 className="text-[11px] font-bold text-slate-700 uppercase tracking-wide truncate" title={col}>{col}</h4>
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#94a3b8' }} hide={data.length > 6} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 9, fill: '#94a3b8' }} />
                    <Tooltip cursor={{ fill: '#f1f5f9' }} contentStyle={{ borderRadius: '6px', fontSize: '11px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                    <Bar dataKey="count" fill={isNumeric ? "#94a3b8" : "#38bdf8"} radius={[2, 2, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
