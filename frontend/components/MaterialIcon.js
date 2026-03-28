export default function MaterialIcon({ name, filled = false, className = "" }) {
  return (
    <span
      className={`material-symbols-outlined ${className}`.trim()}
      style={{
        fontVariationSettings: `'FILL' ${filled ? 1 : 0}, 'wght' 500, 'GRAD' 0, 'opsz' 24`
      }}
      aria-hidden="true"
    >
      {name}
    </span>
  );
}
