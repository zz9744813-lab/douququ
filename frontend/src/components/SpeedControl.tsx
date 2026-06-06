interface Props {
  speed: number;
  onSpeedChange: (speed: number) => void;
}

const SPEED_OPTIONS = [
  { label: '0.5x', value: 0.5 },
  { label: '1x', value: 1 },
  { label: '2x', value: 2 },
  { label: '5x', value: 5 },
  { label: '10x', value: 10 },
];

export default function SpeedControl({ speed, onSpeedChange }: Props) {
  return (
    <div className="flex items-center gap-1">
      {SPEED_OPTIONS.map((opt) => (
        <button key={opt.value}
          onClick={() => onSpeedChange(opt.value)}
          className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
            speed === opt.value ? 'bg-jade-600 text-white' : 'bg-ink-700 text-ink-400 hover:bg-ink-600'
          }`}>
          {opt.label}
        </button>
      ))}
    </div>
  );
}
