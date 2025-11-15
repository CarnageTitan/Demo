import type { CityOption } from '../types';

export const CITY_OPTIONS: CityOption[] = [
  {
    id: 'chicago',
    name: 'Chicago, IL',
    dataUrl: '/data/chicago.json',
    center: [41.88, -87.65],
    zoom: 11,
  },
  {
    id: 'atlanta',
    name: 'Atlanta, GA',
    dataUrl: '/data/atlanta.json',
    center: [33.755, -84.39],
    zoom: 11,
  },
  {
    id: 'phoenix',
    name: 'Phoenix, AZ',
    dataUrl: '/data/phoenix.json',
    center: [33.45, -112.07],
    zoom: 11,
  },
];
