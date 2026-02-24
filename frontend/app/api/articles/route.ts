import { NextResponse } from 'next/server'

// API 代理路由 - 转发到后端服务
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://host.docker.internal:8000'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const limit = searchParams.get('limit') || '50'
  const skip = searchParams.get('skip') || '0'

  try {
    const response = await fetch(
      `${API_BASE_URL}/articles?limit=${limit}&skip=${skip}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      throw new Error(`Backend API error: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('API proxy error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch articles' },
      { status: 500 }
    )
  }
}
