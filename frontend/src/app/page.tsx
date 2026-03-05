export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <h1 className="text-4xl font-bold mb-4">JobScale</h1>
      <p className="text-lg text-gray-600">
        Your AI-powered career accelerator
      </p>
      <div className="mt-8 p-4 bg-gray-100 rounded">
        <h2 className="text-xl font-semibold mb-2">MVP Status</h2>
        <ul className="list-disc list-inside space-y-1 text-sm">
          <li>✅ Backend scaffolded (FastAPI)</li>
          <li>✅ Job scrapers (Greenhouse, Lever, Workable)</li>
          <li>✅ Database models</li>
          <li>⏳ Frontend (coming soon)</li>
          <li>⏳ AI matching engine</li>
          <li>⏳ Auto-application system</li>
        </ul>
      </div>
    </main>
  )
}
