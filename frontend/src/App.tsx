import { BrowserRouter as Router } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

const queryClient = new QueryClient()

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <div className="app">
          <h1>OZON Bot Admin Panel</h1>
          <p>Панель управления в разработке...</p>
        </div>
      </Router>
    </QueryClientProvider>
  )
}

export default App

