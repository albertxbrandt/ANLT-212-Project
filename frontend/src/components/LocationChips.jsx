export default function LocationChips({ locations, selected, onSelect }) {
  return (
    <div className="chips">
      <button type="button" aria-pressed={selected == null} onClick={() => onSelect(null)}>
        All
      </button>
      {locations.map((location) => (
        <button
          type="button"
          key={location.id}
          aria-pressed={selected === location.id}
          onClick={() => onSelect(location.id)}
        >
          {location.name}
        </button>
      ))}
    </div>
  )
}
