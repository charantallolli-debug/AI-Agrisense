const HISTORY_KEY = 'agrisense_prediction_history';

export function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch (err) {
    console.error('Failed to read history:', err);
    return [];
  }
}

export function saveHistory(history) {
  try {
    localStorage.setItem(HISTORY_KEY, JSON.stringify(history));
  } catch (err) {
    console.error('Failed to save history:', err);
  }
}

export function addHistoryEntry(entry) {
  const history = getHistory();
  const newEntry = {
    id: entry.id || Math.random().toString(36).substring(2, 11),
    timestamp: new Date().toISOString(),
    crop: entry.crop || 'Unknown',
    disease: entry.disease || 'Unknown',
    prediction: entry.prediction || 'Unknown',
    confidence: entry.confidence || 0,
    is_healthy: entry.is_healthy ?? false,
    severity_percent: entry.severity_percent ?? 0,
    harmfulness: entry.harmfulness || 'Low',
    ...entry
  };
  
  // Keep last 100 entries
  const updated = [newEntry, ...history].slice(0, 100);
  saveHistory(updated);
  return updated;
}

export function getAnalyticsStats() {
  const history = getHistory();
  
  // Default values when history is empty
  if (history.length === 0) {
    return {
      totalScans: 0,
      healthyCount: 0,
      diseasedCount: 0,
      cropDistribution: [],
      diseaseDistribution: [],
      severityAverages: [],
      recentActivity: []
    };
  }

  const totalScans = history.length;
  let healthyCount = 0;
  let diseasedCount = 0;
  
  const cropsMap = {};
  const diseasesMap = {};
  
  history.forEach(item => {
    if (item.is_healthy) {
      healthyCount++;
    } else {
      diseasedCount++;
    }
    
    // Crop counting
    cropsMap[item.crop] = (cropsMap[item.crop] || 0) + 1;
    
    // Disease counting
    if (!item.is_healthy) {
      const diseaseKey = `${item.crop} - ${item.disease}`;
      diseasesMap[diseaseKey] = (diseasesMap[diseaseKey] || 0) + 1;
    }
  });

  const cropDistribution = Object.entries(cropsMap).map(([name, value]) => ({
    name,
    value
  }));

  const diseaseDistribution = Object.entries(diseasesMap)
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 5);

  // Group scans by date for charts
  const activityMap = {};
  history.slice().reverse().forEach(item => {
    const date = new Date(item.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    if (!activityMap[date]) {
      activityMap[date] = { date, scans: 0, diseased: 0, healthy: 0 };
    }
    activityMap[date].scans++;
    if (item.is_healthy) {
      activityMap[date].healthy++;
    } else {
      activityMap[date].diseased++;
    }
  });

  const recentActivity = Object.values(activityMap);

  return {
    totalScans,
    healthyCount,
    diseasedCount,
    cropDistribution,
    diseaseDistribution,
    recentActivity
  };
}
