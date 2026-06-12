import React, { useState } from 'react';
import { CloudSun, Navigation, MapPin, Wind, Droplets, Sun, AlertTriangle } from 'lucide-react';

export default function WeatherWidget({ weatherData, onFetchWeather, isLoading }) {
  const [cityInput, setCityInput] = useState('');
  const [gpsError, setGpsError] = useState(null);

  const handleGpsClick = () => {
    if (!navigator.geolocation) {
      setGpsError('Geolocation is not supported by your browser.');
      return;
    }
    setGpsError(null);
    navigator.geolocation.getCurrentPosition(
      (position) => {
        onFetchWeather(position.coords.latitude, position.coords.longitude);
      },
      (error) => {
        console.error('GPS error:', error);
        setGpsError('Location access denied or timed out. Using default demo instead.');
        // Fallback to Mumbai
        onFetchWeather(null, null, 'Mumbai');
      },
      { timeout: 8000 }
    );
  };

  const handleCitySubmit = (e) => {
    e.preventDefault();
    if (cityInput.trim()) {
      onFetchWeather(null, null, cityInput.trim());
      setCityInput('');
    }
  };

  const getWeatherIcon = (desc = '') => {
    const d = desc.toLowerCase();
    if (d.includes('rain') || d.includes('drizzle') || d.includes('shower')) return '🌧️';
    if (d.includes('cloud') || d.includes('overcast')) return '☁️';
    if (d.includes('snow') || d.includes('ice')) return '❄️';
    if (d.includes('thunder') || d.includes('storm')) return '⛈️';
    return '☀️';
  };

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
        <div>
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2 flex items-center gap-2">
            <CloudSun className="w-6 h-6 text-primary-600 animate-pulse" />
            Agronomic Field Weather
          </h2>
          <p className="text-sm text-slate-500">Live weather updates to schedule spraying, chemical application, and irrigation.</p>
        </div>

        {/* Input Controls */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={handleGpsClick}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-primary-600 hover:bg-primary-500 disabled:bg-slate-100 text-white disabled:text-slate-400 text-sm font-bold transition-all shadow-sm"
            style={{ minHeight: '48px' }}
          >
            <Navigation className="w-4 h-4" />
            📍 Use My Location
          </button>
          
          <button
            onClick={() => onFetchWeather(null, null, 'Mumbai')}
            disabled={isLoading}
            className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-full bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 text-sm font-bold transition-all"
            style={{ minHeight: '48px' }}
          >
            <MapPin className="w-4 h-4 text-slate-400" />
            🏙️ Demo: Mumbai
          </button>
        </div>

        {/* Search City Box */}
        <form onSubmit={handleCitySubmit} className="flex gap-2">
          <input
            type="text"
            placeholder="Search by city (e.g. Pune, Delhi)..."
            value={cityInput}
            onChange={(e) => setCityInput(e.target.value)}
            disabled={isLoading}
            className="flex-1 px-4 py-2.5 text-sm rounded-full border border-slate-300 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500 bg-slate-50/50"
            style={{ minHeight: '44px' }}
          />
          <button
            type="submit"
            disabled={isLoading || !cityInput.trim()}
            className="px-5 py-2.5 rounded-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-100 text-white disabled:text-slate-400 text-sm font-bold transition-all"
            style={{ minHeight: '44px' }}
          >
            Search
          </button>
        </form>

        {gpsError && (
          <div className="flex items-center gap-2 bg-amber-50 text-amber-800 text-xs px-4 py-2.5 rounded-xl border border-amber-100">
            <AlertTriangle className="w-4 h-4 text-amber-500 shrink-0" />
            <p>{gpsError}</p>
          </div>
        )}

        {/* Loading Overlay */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12 text-slate-500 space-y-3">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-slate-200 border-t-primary-600"></div>
            <p className="text-sm font-semibold">Fetching local weather data...</p>
          </div>
        )}

        {/* Weather Results Card */}
        {!isLoading && weatherData && weatherData.status === 'success' && (
          <div className="bg-slate-50 border border-slate-100 p-6 rounded-2xl space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <div>
                <h3 className="font-serif text-xl font-bold text-slate-900">
                  {weatherData.location}{weatherData.country ? `, ${weatherData.country}` : ''}
                </h3>
                <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mt-0.5">Weather Status</p>
              </div>
              <div className="text-4xl sm:text-5xl font-serif font-black flex items-center gap-2 text-primary-800">
                <span>{getWeatherIcon(weatherData.description)}</span>
                <span>{weatherData.temp_c}°C</span>
              </div>
            </div>

            {/* Weather Parameters Grid */}
            <div className="grid grid-cols-3 gap-4 pt-2 border-t border-b border-slate-200/50 py-4">
              <div className="flex flex-col items-center p-3 bg-white rounded-xl shadow-sm border border-slate-100">
                <Sun className="w-5 h-5 text-amber-500 mb-1" />
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Feels Like</span>
                <span className="text-sm font-bold text-slate-800 mt-0.5">{weatherData.feels_like_c}°C</span>
              </div>
              
              <div className="flex flex-col items-center p-3 bg-white rounded-xl shadow-sm border border-slate-100">
                <Droplets className="w-5 h-5 text-sky-500 mb-1" />
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Humidity</span>
                <span className="text-sm font-bold text-slate-800 mt-0.5">{weatherData.humidity}%</span>
              </div>

              <div className="flex flex-col items-center p-3 bg-white rounded-xl shadow-sm border border-slate-100">
                <Wind className="w-5 h-5 text-slate-500 mb-1" />
                <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Wind Speed</span>
                <span className="text-sm font-bold text-slate-800 mt-0.5">{weatherData.wind_ms} m/s</span>
              </div>
            </div>

            {/* Weather Tip Box */}
            {weatherData.farming_tip && (
              <div className="bg-gradient-to-br from-primary-50 to-primary-100/50 border border-primary-200 p-5 rounded-xl">
                <p className="text-xs font-black text-primary-800 uppercase tracking-widest mb-1.5 flex items-center gap-1.5">
                  <Sun className="w-4 h-4 text-primary-600 shrink-0" />
                  Agronomic Advisories
                </p>
                <p className="text-sm text-slate-700 leading-relaxed font-semibold">
                  {weatherData.farming_tip}
                </p>
              </div>
            )}

            {weatherData.source === 'demo' && (
              <p className="text-[10px] text-slate-400 text-center italic">
                Showing Mumbai demo weather. Live weather data uses the free Open-Meteo API.
              </p>
            )}
          </div>
        )}

        {!isLoading && !weatherData && (
          <div className="flex flex-col items-center justify-center py-10 text-center text-slate-400 border border-dashed border-slate-200 rounded-2xl">
            <CloudSun className="w-12 h-12 text-slate-300 mb-2" />
            <p className="text-sm font-bold text-slate-500">No weather data loaded</p>
            <p className="text-xs text-slate-400 mt-1 max-w-[280px]">Select location or demo to check local weather forecasts.</p>
          </div>
        )}
      </div>
    </div>
  );
}
