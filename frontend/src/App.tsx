import { useEffect, useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
  fetchDailyStats, fetchHourlyStats, fetchCitiesStats,
  fetchTopZones, fetchCities,
  DailyStat, HourlyStat, CityStat, ZoneStat
} from './api';
import './index.css';

// ─── Couleurs du dashboard ────────────────────────────────────
const COLORS = ['#38bdf8', '#818cf8', '#34d399', '#fb923c', '#f472b6'];

export default function App() {
  // ─── État ──────────────────────────────────────────────────
  const [cities, setCities]           = useState<string[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>('');
  const [daily, setDaily]             = useState<DailyStat[]>([]);
  const [hourly, setHourly]           = useState<HourlyStat[]>([]);
  const [citiesStats, setCitiesStats] = useState<CityStat[]>([]);
  const [zones, setZones]             = useState<ZoneStat[]>([]);
  const [loading, setLoading]         = useState(true);

  // ─── Chargement initial ───────────────────────────────────
  useEffect(() => {
    Promise.all([
      fetchCities(),
      fetchCitiesStats(),
      fetchTopZones(),
    ]).then(([c, cs, z]) => {
      setCities(c);
      setCitiesStats(cs);
      setZones(z);
      setLoading(false);
    });
  }, []);

  // ─── Rechargement quand la ville change ───────────────────
  useEffect(() => {
    const city = selectedCity || undefined;
    Promise.all([
      fetchDailyStats(city),
      fetchHourlyStats(city),
    ]).then(([d, h]) => {
      // Garder seulement les 30 derniers jours pour le graphe
      const sorted = d.sort((a, b) => a.date.localeCompare(b.date));
      setDaily(sorted.slice(-30));
      setHourly(h.sort((a, b) => a.hour - b.hour));
    });
  }, [selectedCity]);

  // ─── Stats globales ───────────────────────────────────────
  const totalTrips    = citiesStats.reduce((s, c) => s + c.trip_count, 0);
  const avgDistance   = citiesStats.length
    ? (citiesStats.reduce((s, c) => s + c.avg_distance, 0) / citiesStats.length).toFixed(1)
    : 0;
  const peakHour      = hourly.length
    ? hourly.reduce((a, b) => a.trip_count > b.trip_count ? a : b).hour
    : '-';
  const topCity       = citiesStats.length ? citiesStats[0].city : '-';

  if (loading) return <div className="loading">Chargement du dashboard...</div>;

  return (
    <div className="dashboard">

      {/* ── En-tête ── */}
      <div className="header">
        <h1>Urban Transport Analytics</h1>
        <p>Plateforme Big Data d'analyse des données de transport urbain</p>
      </div>

      {/* ── Filtre ville ── */}
      <div className="filters">
        <select value={selectedCity} onChange={e => setSelectedCity(e.target.value)}>
          <option value="">Toutes les villes</option>
          {cities.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* ── Cartes statistiques ── */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="value">{totalTrips.toLocaleString()}</div>
          <div className="label">Total trajets</div>
        </div>
        <div className="stat-card">
          <div className="value">{citiesStats.length}</div>
          <div className="label">Villes analysées</div>
        </div>
        <div className="stat-card">
          <div className="value">{avgDistance} km</div>
          <div className="label">Distance moyenne</div>
        </div>
        <div className="stat-card">
          <div className="value">{peakHour}h</div>
          <div className="label">Heure de pointe</div>
        </div>
        <div className="stat-card">
          <div className="value">{topCity}</div>
          <div className="label">Ville la plus active</div>
        </div>
      </div>

      {/* ── Graphiques ── */}
      <div className="charts-grid">

        {/* Trajets par jour */}
        <div className="chart-card">
          <h2>Trajets par jour (30 derniers jours)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={daily}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="date" tick={{ fill: '#94a3b8', fontSize: 10 }}
                     tickFormatter={d => d.slice(5)} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Line type="monotone" dataKey="trip_count" stroke="#38bdf8"
                    strokeWidth={2} dot={false} name="Trajets" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Heures de pointe */}
        <div className="chart-card">
          <h2>Heures de pointe</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={hourly}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis dataKey="hour" tick={{ fill: '#94a3b8', fontSize: 10 }}
                     tickFormatter={h => `${h}h`} />
              <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }}
                       formatter={(v) => [v, 'Trajets']}
                       labelFormatter={h => `${h}h00`} />
              <Bar dataKey="trip_count" fill="#818cf8" name="Trajets" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Distance moyenne par ville */}
        <div className="chart-card">
          <h2>Distance moyenne par ville (km)</h2>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={citiesStats} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <YAxis dataKey="city" type="category" tick={{ fill: '#94a3b8', fontSize: 10 }} />
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Bar dataKey="avg_distance" fill="#34d399" name="Distance moy." radius={[0,4,4,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Top zones */}
        <div className="chart-card">
          <h2> Top zones de départ</h2>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie data={zones} dataKey="trip_count" nameKey="zone"
                    cx="50%" cy="50%" outerRadius={90}
                    label={(entry) => String(entry.name)}>               {zones.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

      </div>
    </div>
  );
}


