'use client'

import useSWR from 'swr'
import { useState } from 'react'
import Link from 'next/link'

interface Article {
  id: number
  title: string
  url: string
  published_date: string | null
  summary: string | null
  content: string | null
  translation: string | null
  translated_at: string | null
  content_translation: string | null
  content_translated_at: string | null
  created_at: string
  notified: boolean
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function Home() {
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [showContent, setShowContent] = useState(false)
  const [showTranslation, setShowTranslation] = useState(false)
  const { data: articles, error, isLoading, mutate } = useSWR<Article[]>('/api/articles', fetcher, {
    refreshInterval: 60000, // 每分钟刷新
  })

  // 解析翻译内容
  const parseTranslation = (translation: string | null) => {
    if (!translation) return null
    try {
      return JSON.parse(translation)
    } catch {
      return null
    }
  }

  // 删除文章
  const handleDelete = async (id: number, title: string) => {
    if (!confirm(`确定要删除这篇文章吗？\n\n${title.substring(0, 50)}...`)) {
      return
    }
    
    try {
      const response = await fetch(`/api/articles/${id}`, {
        method: 'DELETE',
      })
      
      if (response.ok) {
        alert('文章已删除')
        mutate() // 重新加载列表
      } else {
        const data = await response.json()
        alert(`删除失败：${data.detail || '未知错误'}`)
      }
    } catch (error) {
      alert(`删除失败：${error}`)
    }
  }

  if (error) return <div className="text-center text-red-500 mt-10">加载失败</div>
  if (isLoading) return <div className="text-center mt-10">加载中...</div>

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* 头部 */}
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div></div>
            <Link href="/translations" className="text-blue-600 hover:underline">
              🌐 查看翻译文章 →
            </Link>
          </div>
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
            articles.map((article) => {
              const translation = parseTranslation(article.translation)
              return (
                <article key={article.id} className="article-card">
                  {/* 优先显示翻译后的标题 */}
                  {translation?.title ? (
                    <>
                      <h2 className="article-title text-purple-700">
                        <a
                          href={article.url}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          {translation.title}
                        </a>
                      </h2>
                      <p className="text-sm text-gray-500 mb-3 italic">
                        原标题：{article.title}
                      </p>
                    </>
                  ) : (
                    <h2 className="article-title">
                      <a
                        href={article.url}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {article.title}
                      </a>
                    </h2>
                  )}
                  
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
                  {/* 查看翻译按钮 - 只有有翻译内容时才显示 */}
                  {translation && (
                    <button
                      onClick={() => {
                        setSelectedArticle(article)
                        setShowTranslation(true)
                      }}
                      className="text-purple-600 hover:underline"
                    >
                      🌐 查看翻译
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(article.id, article.title)}
                    className="text-red-600 hover:underline"
                  >
                    🗑️ 删除
                  </button>
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
              )
            })
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

        {/* 翻译查看模态框 */}
        {showTranslation && selectedArticle && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
              {/* 头部 */}
              <div className="p-6 border-b border-gray-200 bg-purple-50">
                <h3 className="text-2xl font-bold text-purple-800 mb-2">
                  🌐 中文翻译
                </h3>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-purple-600">
                    {parseTranslation(selectedArticle.translation)?.title || selectedArticle.title}
                  </span>
                  <button
                    onClick={() => setShowTranslation(false)}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ✕
                  </button>
                </div>
              </div>

              {/* 内容区域 */}
              <div className="flex-1 overflow-y-auto p-6">
                {(() => {
                  const trans = parseTranslation(selectedArticle.translation)
                  const fullTrans = parseTranslation(selectedArticle.content_translation)

                  if (!trans && !fullTrans) {
                    return (
                      <div className="text-center text-gray-500 py-10">
                        暂无翻译内容
                      </div>
                    )
                  }

                  // 优先使用全文翻译
                  const displayData = fullTrans || trans

                  return (
                    <div className="prose max-w-none">
                      {/* 翻译标题 */}
                      {displayData?.title && (
                        <div className="bg-purple-50 rounded-lg p-4 mb-4">
                          <h4 className="text-lg font-semibold text-purple-700 mb-2">
                            📌 标题
                          </h4>
                          <p className="text-purple-900 text-xl font-medium">
                            {displayData.title}
                          </p>
                        </div>
                      )}

                      {/* 翻译摘要 */}
                      {displayData?.summary && (
                        <div className="bg-gray-50 rounded-lg p-4 mb-4">
                          <h4 className="text-lg font-semibold text-gray-700 mb-2">
                            📝 摘要翻译
                          </h4>
                          <p className="text-gray-700 whitespace-pre-wrap leading-relaxed">
                            {displayData.summary}
                          </p>
                        </div>
                      )}

                      {/* 全文翻译 */}
                      {fullTrans?.content && (
                        <div className="bg-blue-50 rounded-lg p-4 mb-4">
                          <h4 className="text-lg font-semibold text-blue-700 mb-2">
                            📖 全文翻译
                          </h4>
                          <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
                            {fullTrans.content}
                          </p>
                        </div>
                      )}

                      {/* 原文信息 */}
                      <div className="mt-6 pt-4 border-t border-gray-200">
                        <p className="text-sm text-gray-500">
                          <strong>原标题：</strong>{selectedArticle.title}
                        </p>
                        {fullTrans && selectedArticle.content_translated_at && (
                          <p className="text-sm text-gray-500 mt-1">
                            <strong>全文翻译时间：</strong>
                            {new Date(selectedArticle.content_translated_at).toLocaleString('zh-CN')}
                          </p>
                        )}
                        {!fullTrans && selectedArticle.translated_at && (
                          <p className="text-sm text-gray-500 mt-1">
                            <strong>翻译时间：</strong>
                            {new Date(selectedArticle.translated_at).toLocaleString('zh-CN')}
                          </p>
                        )}
                      </div>
                    </div>
                  )
                })()}
              </div>

              {/* 底部按钮 */}
              <div className="p-4 border-t border-gray-200 flex justify-between">
                <a
                  href={selectedArticle.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  查看原文链接 →
                </a>
                <button
                  onClick={() => setShowTranslation(false)}
                  className="px-4 py-2 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
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
