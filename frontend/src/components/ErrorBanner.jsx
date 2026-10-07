export default function ErrorBanner({ message }) {
  if (!message) return null
  return (
    <p className="banner" role="alert">
      {message}
    </p>
  )
}
