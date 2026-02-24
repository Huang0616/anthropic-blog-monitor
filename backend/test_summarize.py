#!/usr/bin/env python3
"""手动测试摘要生成"""

import asyncio
import sys
sys.path.insert(0, '/app')

from summarizer import Summarizer

async def test_summarize():
    summarizer = Summarizer()
    
    # 测试文章
    title = "Advanced Tool Use"
    content = """Claude can now discover, learn, and execute tools dynamically to enable agents that take action in the real world. Here's how.

Today, we're launching Tool Use Beta, which allows Claude to discover available tools, learn how to use them from documentation, and execute them to complete complex tasks. This represents a significant step forward in Claude's capabilities - moving from a purely conversational AI to one that can take actions in the real world.

## Key Capabilities

With Tool Use, Claude can now:

1. **Discover Tools**: Automatically find available tools through MCP (Model Context Protocol) servers
2. **Learn Dynamically**: Read tool documentation and understand how to use each tool
3. **Execute Actions**: Call tools with appropriate parameters to complete tasks
4. **Chain Operations**: Combine multiple tool calls to accomplish complex workflows

## Implementation

The implementation uses a flexible architecture that allows Claude to:

- Parse tool schemas and understand input/output requirements
- Generate appropriate tool calls based on user requests
- Handle errors and retry failed operations
- Provide clear explanations of tool usage to users

## Example Use Cases

Here are some examples of what Claude can now do with Tool Use:

### Database Operations
Claude can connect to databases, run queries, and return results - all while explaining what it's doing.

### File Operations
Claude can read, write, and manipulate files on your system with proper permissions.

### API Integration
Claude can call external APIs to fetch data, post updates, or integrate with third-party services.

## Getting Started

To start using Tool Use with Claude:

1. Install the Claude Code CLI
2. Configure MCP servers for the tools you want to use
3. Start a Claude session and ask it to help with tasks that require tool use

We're excited to see what developers build with this new capability!
"""
    
    print(f"测试文章：{title}")
    print(f"内容长度：{len(content)} 字符")
    print("\n生成摘要中...\n")
    
    summary = await summarizer.summarize(title, content)
    
    print("\n" + "=" * 60)
    print("生成的摘要:")
    print("=" * 60)
    print(summary)
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(test_summarize())
