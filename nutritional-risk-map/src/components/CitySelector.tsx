import type { CityOption } from '../types';

interface Props {
  options: CityOption[];
  value: string;
  onChange: (id: string) => void;
}

export const CitySelector = ({ options, value, onChange }: Props) => {
  return (
    <label className="city-selector">
      <span>Select a city dataset</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </label>
  );
};
