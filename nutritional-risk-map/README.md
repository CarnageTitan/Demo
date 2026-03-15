# Neighborhood Nutrition Risk Explorer

This Vite + React app highlights food desert conditions by combining synthetic public indicators for select U.S. cities. Users can:

- Choose Chicago, Atlanta, or Phoenix from a dropdown.
- Load each city's per-neighborhood dataset (income, transit access, grocery proximity, store density, chronic disease prevalence).
- View an interactive Leaflet map with neighborhoods color-coded from low to severe nutrition risk.
- Click any neighborhood to see its risk score, key drivers, and an AI-style intervention idea (mobile markets, corner store incentives, transit support, community education, etc.).

## Getting Started

```bash
npm install
npm run dev
```

Then open the printed local URL (usually http://localhost:5173).

## Project Structure

- `src/data/cities.ts` – catalog of available city datasets.
- `public/data/*.json` – simple GeoJSON-like files with neighborhood metrics for each city.
- `src/lib/risk.ts` – scoring, driver summary, and recommendation helpers.
- `src/components` – UI pieces: city selector, map, legend, and detail panel.

## Customizing

1. Add another JSON file under `public/data/` that follows the existing schema.
2. Append your city entry to `CITY_OPTIONS` with its map center/zoom and data URL.
3. Adjust the weighting logic in `src/lib/risk.ts` if you need different indicators or thresholds.

## Available Scripts

- `npm run dev` – start the Vite dev server.
- `npm run build` – create a production build.
- `npm run preview` – serve the production build locally.
