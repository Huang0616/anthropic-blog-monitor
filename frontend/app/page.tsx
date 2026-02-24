'use client'

import useSWR from 'swr'

interface Article {
  id: number
  title: string
  url: string
  published_date: string | null
  summary: string | null
  created_at: string
  notified: boolean
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function Home() {
  const { data: articles, error, isLoading } = useSWR<Article[]>('/api/articles', fetcher, {
    refreshInterval: 60000, // 每分钟刷新
  })

  if (error) return <div className="text-center text-red-500 mt-10">加载失败</div>
  if (isLoading) return <div className="text-center mt-10">加载中...</div>

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* 头部 */}
        <header className="mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            📰 Anthropic Blog Monitor
          </h1>
          <p className="text-gray-600">
            自动抓取 Anthropic 官方博客，AI 生成中文摘要
          </p>
        </header>

        {/* 状态栏 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-sm text-blue-800">
                ✅ 服务运行中 · 每日上午 9 点自动更新
              </span>
            </div>
            <a
              href="/api/scrape"
              target="_blank"
              className="text-sm text-blue-600 hover:underline"
            >
              手动刷新 →
            </a>
          </div>
        </div>

        {/* 文章列表 */}
        <div className="space-y-6">
          {articles && articles.length > 0 ? (
            articles.map((article) => (
              <article key={article.id} className="article-card">
                <h2 className="article-title">
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    {article.title}
                  </a>
                </h2>
                
                {article.summary && (
                  <p className="article-summary">{article.summary}</p>
                )}
                
                <div className="article-meta">
                  <span>
                    📅 {article.published_date 
                      ? new Date(article.published_date).toLocaleDateString('zh-CN')
                      : new Date(article.created_at).toLocaleDateString('zh-CN')
                    }
                  </span>
                  {article.notified && <span>🔔 已推送</span>}
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline ml-auto"
                  >
                    阅读原文 →
                  </a>
                </div>
              </article>
            ))
          ) : (
            <div className="text-center text-gray-500 py-10">
              暂无文章，等待首次爬取...
            </div>
          )}
        </div>

        {/* 页脚 */}
        <footer className="mt-12 text-center text-sm text-gray-400">
          <p>Powered by FastAPI + Next.js + Docker 🐳</p>
        </footer>
      </div>
    </main>
  )
}
