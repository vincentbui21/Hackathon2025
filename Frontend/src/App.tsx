import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-background text-foreground">
      <div className="flex gap-8 mb-8">
        <a href="https://vite.dev" target="_blank" className="transition-transform hover:scale-110">
          <img src={viteLogo} className="h-24 w-24" alt="Vite logo" />
        </a>
        <a href="https://react.dev" target="_blank" className="transition-transform hover:scale-110">
          <img src={reactLogo} className="h-24 w-24 animate-spin-slow" alt="React logo" />
        </a>
      </div>
      <h1 className="text-4xl font-bold mb-8">Vite + React</h1>
      <div className="bg-card p-8 rounded-lg shadow-lg">
        <button
          onClick={() => setCount((count) => count + 1)}
          className="px-6 py-3 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors font-medium"
        >
          count is {count}
        </button>
        <p className="mt-4 text-muted-foreground">
          Edit <code className="bg-muted px-2 py-1 rounded text-sm">src/App.tsx</code> and save to test HMR
        </p>
      </div>
      <p className="mt-8 text-muted-foreground">
        Click on the Vite and React logos to learn more
      </p>
    </div>
  )
}

export default App
