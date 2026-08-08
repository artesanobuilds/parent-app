import { Routes, Route, Navigate } from 'react-router-dom'
import CMSLayout from './components/layout/CMSLayout'
import { Dashboard } from './pages/Dashboard'
import { ArticleList } from './pages/ArticleList'
import { ArticleEditor } from './pages/ArticleEditor'
import { CategoryList } from './pages/CategoryList'
import { CategoryEditor } from './pages/CategoryEditor'
import { EmailSync } from './pages/EmailSync'
import { CalendarSync } from './pages/CalendarSync'
import { LegalList } from './pages/LegalList'
import { LegalEditor } from './pages/LegalEditor'
import { Login } from './pages/Login'
import { Toaster } from './components/shared/Toast'

export default function App() {
  return (
    <>
      <Toaster />
      <Routes>
        <Route path="login" element={<Login />} />
        <Route element={<CMSLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="articles" element={<ArticleList />} />
          <Route path="articles/new" element={<ArticleEditor />} />
          <Route path="articles/:id" element={<ArticleEditor />} />
          <Route path="categories" element={<CategoryList />} />
          <Route path="categories/:id" element={<CategoryEditor />} />
          <Route path="email-sync" element={<EmailSync />} />
          <Route path="calendar-sync" element={<CalendarSync />} />
          <Route path="legal" element={<LegalList />} />
          <Route path="legal/:slug" element={<LegalEditor />} />
          <Route path="*" element={<Navigate to="" replace />} />
        </Route>
      </Routes>
    </>
  )
}
