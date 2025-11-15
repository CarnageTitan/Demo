import { useEffect, useMemo, useState } from 'react';
import './App.css';
import { CITY_OPTIONS } from './data/cities';
import type { CityDataset, NeighborhoodWithScore } from './types';
import {
  calculateRiskScore,
  classifyRiskLevel,
  describeDrivers,
  recommendIntervention,
} from './lib/risk';
import { CitySelector } from './components/CitySelector';
import { RiskMap } from './components/RiskMap';
import { NeighborhoodPanel } from './components/NeighborhoodPanel';
import { RiskLegend } from './components/RiskLegend';

function App() {
  const [cityId, setCityId] = useState(CITY_OPTIONS[0].id);
  const [cityData, setCityData] = useState<CityDataset | null>(null);
  const [selectedNeighborhoodId, setSelectedNeighborhoodId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const cityOption = CITY_OPTIONS.find((option) => option.id === cityId) ?? CITY_OPTIONS[0];

  useEffect(() => {
    const controller = new AbortController();
    const loadCityData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch(cityOption.dataUrl, { signal: controller.signal });
        if (!response.ok) {
          throw new Error(`Unable to load dataset (${response.status})`);
        }
        const payload = (await response.json()) as CityDataset;
        setCityData(payload);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') return;
        setError(err instanceof Error ? err.message : 'Something went wrong.');
        setCityData(null);
      } finally {
        setIsLoading(false);
      }
    };

    loadCityData();
    return () => controller.abort();
  }, [cityOption]);

  const scoredNeighborhoods = useMemo<NeighborhoodWithScore[]>(() => {
    if (!cityData) return [];
    return [...cityData.neighborhoods]
      .map((neighborhood) => {
        const riskScore = calculateRiskScore(neighborhood);
        return {
          ...neighborhood,
          riskScore,
          riskLevel: classifyRiskLevel(riskScore),
          driverSummary: describeDrivers(neighborhood),
          recommendation: recommendIntervention(neighborhood),
        };
      })
      .sort((a, b) => b.riskScore - a.riskScore);
  }, [cityData]);

  useEffect(() => {
    if (scoredNeighborhoods.length) {
      setSelectedNeighborhoodId(scoredNeighborhoods[0].id);
    } else {
      setSelectedNeighborhoodId(null);
    }
  }, [scoredNeighborhoods]);

  const selectedNeighborhood = scoredNeighborhoods.find(
    (neighborhood) => neighborhood.id === selectedNeighborhoodId,
  );

  const headlineRisk = scoredNeighborhoods[0];
  const topThree = scoredNeighborhoods.slice(0, 3);

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Food access insights</p>
          <h1>Neighborhood Nutrition Risk Explorer</h1>
          <p>
            Identify food desert pressures by combining access, affordability, and chronic disease
            signals. Pick a city to see the neighborhoods that need the fastest response.
          </p>
        </div>
        <CitySelector options={CITY_OPTIONS} value={cityId} onChange={setCityId} />
      </header>

      <main className="app-main">
        <section className="insights-panel">
          {cityData?.description && <p className="dataset-description">{cityData.description}</p>}
          {isLoading && <div className="notice">Loading neighborhood data…</div>}
          {error && !isLoading && <div className="notice error">{error}</div>}

          {headlineRisk && !isLoading && !error && (
            <article className="panel highlight-panel">
              <p className="eyebrow">Highest risk right now</p>
              <h2>{headlineRisk.name}</h2>
              <p>{headlineRisk.driverSummary}</p>
              <div className="highlight-metrics">
                <div>
                  <span className="eyebrow">Risk score</span>
                  <strong>{Math.round(headlineRisk.riskScore * 100)}</strong>
                </div>
                <div>
                  <span className="eyebrow">Intervention idea</span>
                  <strong>{headlineRisk.recommendation}</strong>
                </div>
              </div>
            </article>
          )}

          {!!topThree.length && (
            <div className="panel list-panel">
              <p className="eyebrow">Top risk neighborhoods</p>
              <ul className="risk-list">
                {topThree.map((neighborhood) => (
                  <li
                    key={neighborhood.id}
                    className={neighborhood.id === selectedNeighborhoodId ? 'active' : ''}
                    onClick={() => setSelectedNeighborhoodId(neighborhood.id)}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault();
                        setSelectedNeighborhoodId(neighborhood.id);
                      }
                    }}
                    role="button"
                    tabIndex={0}
                    aria-pressed={neighborhood.id === selectedNeighborhoodId}
                  >
                    <div>
                      <strong>{neighborhood.name}</strong>
                      <p>{neighborhood.driverSummary}</p>
                    </div>
                    <span>{Math.round(neighborhood.riskScore * 100)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <NeighborhoodPanel neighborhood={selectedNeighborhood} />
        </section>

        <section className="map-panel">
          {scoredNeighborhoods.length ? (
            <RiskMap
              neighborhoods={scoredNeighborhoods}
              center={cityOption.center}
              zoom={cityOption.zoom}
              selectedId={selectedNeighborhoodId}
              onSelect={setSelectedNeighborhoodId}
            />
          ) : (
            <div className="panel empty-panel map-placeholder">
              Select a city and load data to view the map.
            </div>
          )}
          <RiskLegend />
        </section>
      </main>
    </div>
  );
}

export default App;
