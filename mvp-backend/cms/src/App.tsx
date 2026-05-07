import { Routes, Route, Navigate } from 'react-router-dom'
import CMSLayout from './components/layout/CMSLayout'
import { Dashboard } from './pages/Dashboard'
import { ArticleList } from './pages/ArticleList'
import { ArticleEditor } from './pages/ArticleEditor'
import { CommunityPostList } from './pages/CommunityPostList'
import { CommunityPostEditor } from './pages/CommunityPostEditor'
import { CategoryList } from './pages/CategoryList'
import { CategoryEditor } from './pages/CategoryEditor'
import { Toaster } from './components/shared/Toast'

export default function App() {
  return (
    <>
      <Toaster />
      <Routes>
        <Route element={<CMSLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="articles" element={<ArticleList />} />
          <Route path="articles/new" element={<ArticleEditor />} />
          <Route path="articles/:id" element={<ArticleEditor />} />
          <Route path="community" element={<CommunityPostList />} />
          <Route path="community/new" element={<CommunityPostEditor />} />
          <Route path="community/:id" element={<CommunityPostEditor />} />
          <Route path="categories" element={<CategoryList />} />
          <Route path="categories/:id" element={<CategoryEditor />} />
          <Route path="*" element={<Navigate to="" replace />} />
        </Route>
      </Routes>
    </>
  )
}
