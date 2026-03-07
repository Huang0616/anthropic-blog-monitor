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
  translation: string | null
  translated_at: string | null
  created_at: string
}

const fetcher = (url: string) => fetch(url).then((res) => res.json())

export default function TranslationsPage() {
  const { data: articles, error, isLoading } = useSWR<Article[]>('/api/articles', fetcher, {
    refreshInterval: 60000,
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

  if (error) return <div className="text-center text-red-500 mt-10">加载失败</div>
  if (isLoading) return <div className="text-center mt-10">加载中...</div>

  // 过滤出有翻译的文章
  const translatedArticles = articles?.filter(a => a.translation) || []

  return (
    <main className="min-h-screen p-8">
      <div className="max-w-4xl mx-auto">
        {/* 头部 */}
        <header className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <Link href="/" className="text-blue-600 hover:underline">
              ← 返回主页
            </Link>
          </div>
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🌐 翻译文章列表
          </h1>
          <p className="text-gray-600">
            AI 翻译的 Anthropic 博客文章（标题 + 摘要）
          </p>
        </header>

        {/* 统计信息 */}
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-8">
          <span className="text-sm text-purple-800">
            📊 共 {translatedArticles.length} 篇已翻译文章
          </span>
        </div>

        {/* 文章列表 */}
        <div className="space-y-6">
          {translatedArticles.length > 0 ? (
            translatedArticles.map((article) => {
              const translation = parseTranslation(article.translation)
              return (
                <article key={article.id} className="article-card">
                  {/* 中文标题 */}
                  {translation?.title && (
                    <h2 className="article-title text-purple-700">
                      {translation.title}
                    </h2>
                  )}
                  
                  {/* 原英文标题 */}
                  <p className="text-sm text-gray-500 mb-3 italic">
                    原标题：{article.title}
                  </p>
                  
                  {/* 中文摘要 */}
                  {translation?.summary && (
                    <div className="bg-gray-50 rounded-lg p-4 mb-4">
                      <h3 className="text-sm font-semibold text-gray-700 mb-2">
                        📝 中文摘要
                      </h3>
                      <p className="text-gray-600 whitespace-pre-wrap">
                        {translation.summary}
                      </p>
                    </div>
                  )}
                  
                  {/* 英文摘要（可折叠） */}
                  {article.summary && (
                    <details className="mb-4">
                      <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                        查看英文摘要
                      </summary>
                      <p className="mt-2 text-gray-500 text-sm whitespace-pre-wrap pl-4 border-l-2 border-gray-300">
                        {article.summary}
                      </p>
                    </details>
                  )}
                  
                  {/* 元信息 */}
                  <div className="article-meta">
                    <span>
                      📅 {article.published_date 
                        ? new Date(article.published_date).toLocaleDateString('zh-CN')
                        : new Date(article.created_at).toLocaleDateString('zh-CN')
                      }
                    </span>
                    {article.translated_at && (
                      <span>
                        🌐 翻译于 {new Date(article.translated_at).toLocaleDateString('zh-CN')}
                      </span>
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
              )
            })
          ) : (
            <div className="text-center text-gray-500 py-10">
              暂无翻译文章，等待新文章推送...
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
