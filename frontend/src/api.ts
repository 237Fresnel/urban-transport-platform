import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

// Types 
export interface DailyStat {
  date: string;
  trip_count: number;
}

export interface HourlyStat {
  hour: number;
  trip_count: number;
}

export interface CityStat {
  city: string;
  avg_distance: number;
  trip_count: number;
}

export interface ZoneStat {
  zone: string;
  trip_count: number;
}

export interface WeekdayStat {
  city: string;
  day_of_week: string;
  trip_count: number;
}

// Appels API 
export const fetchDailyStats = (city?: string) =>
  api.get<DailyStat[]>('/stats/daily', { params: { city } }).then(r => r.data);

export const fetchHourlyStats = (city?: string) =>
  api.get<HourlyStat[]>('/stats/hourly', { params: { city } }).then(r => r.data);

export const fetchCitiesStats = () =>
  api.get<CityStat[]>('/stats/cities').then(r => r.data);

export const fetchTopZones = () =>
  api.get<ZoneStat[]>('/top-zones').then(r => r.data);

export const fetchCities = () =>
  api.get<string[]>('/cities').then(r => r.data);

export const fetchWeekdayStats = () =>
  api.get<WeekdayStat[]>('/stats/weekday').then(r => r.data);