'use client'

import useSWR from 'swr'
import { useState } from 'react'

interface Article {
  id: number
  title: string
  url: string
  published_date: string | null
  summary: string | null
  content: string | null
  created_at: string
  notified: boolean
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function Home() {
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [showContent, setShowContent] = useState(false)
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
                  {article.content && (
                    <button
                      onClick={() => {
                        setSelectedArticle(article)
                        setShowContent(true)
                      }}
                      className="text-green-600 hover:underline"
                    >
                      📄 查看原文
                    </button>
                  )}
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

        {/* 原文查看模态框 */}
        {showContent && selectedArticle && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
              {/* 头部 */}
              <div className="p-6 border-b border-gray-200">
                <h3 className="text-2xl font-bold text-gray-800 mb-2">
                  {selectedArticle.title}
                </h3>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">
                    📅 {selectedArticle.published_date 
                      ? new Date(selectedArticle.published_date).toLocaleDateString('zh-CN')
                      : new Date(selectedArticle.created_at).toLocaleDateString('zh-CN')
                    }
                  </span>
                  <button
                    onClick={() => setShowContent(false)}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* 内容区域 */}
              <div className="flex-1 overflow-y-auto p-6">
                {selectedArticle.content ? (
                  <div className="prose max-w-none">
                    <div className="bg-gray-50 rounded-lg p-4 mb-4">
                      <h4 className="text-lg font-semibold text-gray-700 mb-2">
                        📝 AI 摘要
                      </h4>
                      <p className="text-gray-600 whitespace-pre-wrap">
                        {selectedArticle.summary || '暂无摘要'}
                      </p>
                    </div>
                    
                    <div>
                      <h4 className="text-lg font-semibold text-gray-700 mb-2">
                        📖 原文内容
                      </h4>
                      <div className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                        {selectedArticle.content}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-10">
                    原文内容暂未提取
                  </div>
                )}
              </div>

              {/* 底部按钮 */}
              <div className="p-4 border-t border-gray-200 flex justify-between">
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  在浏览器打开 →
                </a>
                <button
                  onClick={() => setShowContent(false)}
                  className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
                >
                  关闭
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 页脚 */}
        <footer className="mt-12 text-center text-sm text-gray-400">
          <p>Powered by FastAPI + Next.js + Docker 🐳</p>
        </footer>
      </div>
    </main>
  )
}
