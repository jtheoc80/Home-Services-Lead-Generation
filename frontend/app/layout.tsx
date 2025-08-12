import HealthBanner from '../components/HealthBanner'
import '../styles/globals.css'

export const metadata = {
  title: 'Lead Ledger Pro',
  description: 'Home Services Lead Generation Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <HealthBanner />
        {children}
      </body>
    </html>
  )
}