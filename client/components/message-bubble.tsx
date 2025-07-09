"use client"

import { useMemo } from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card } from "@/components/ui/card"
import { User, Bot } from "lucide-react"
import { MarkdownRenderer } from "./markdown-renderer"
import { ThinkingSection } from "./thinking-section"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: string
}

interface MessageBubbleProps {
  message: Message
  isLoading?: boolean
}

type Segment = {
  type: "thinking" | "normal"
  content: string
}

// 解析器：将内容解析为多个段
function parseStreamContent(content: string): Segment[] {
  const segments: Segment[] = []
  const thinkingOpen = "<think>"
  const thinkingClose = "</think>"

  let index = 0
  while (index < content.length) {
    const openIndex = content.indexOf(thinkingOpen, index)
    const closeIndex = content.indexOf(thinkingClose, index)

    if (openIndex !== -1 && (openIndex < closeIndex || closeIndex === -1)) {
      // 添加之前的正常内容
      if (openIndex > index) {
        segments.push({
          type: "normal",
          content: content.slice(index, openIndex),
        })
      }
      index = openIndex + thinkingOpen.length
    }

    if (closeIndex !== -1 && closeIndex > index) {
      // 添加思考内容
      segments.push({
        type: "thinking",
        content: content.slice(index, closeIndex),
      })
      index = closeIndex + thinkingClose.length
    } else {
      // 没有结束标签，可能是思考未完成
      const remaining = content.slice(index)
      if (content.includes(thinkingOpen) && !content.includes(thinkingClose)) {
        // 思考未闭合，保留当前内容为思考
        segments.push({
          type: "thinking",
          content: remaining,
        })
      } else {
        // 作为普通文本
        segments.push({
          type: "normal",
          content: remaining,
        })
      }
      break
    }
  }

  return segments
}

export function MessageBubble({ message, isLoading }: MessageBubbleProps) {
  const isUser = message.role === "user"

  const segments = useMemo(() => {
    return isUser
      ? [{ type: "normal", content: message.content }]
      : parseStreamContent(message.content)
  }, [message.content, isUser])

  return (
    <div className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <Avatar className="w-8 h-8 mt-1">
          <AvatarFallback className="bg-blue-100 text-blue-600">
            <Bot className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}

      <div className={`max-w-[70%] ${isUser ? "order-first" : ""}`}>
        {segments.map((seg, i) => {
          const content = seg.content.trim()
          if (!content) return null

          if (seg.type === "thinking") {
            return <ThinkingSection key={i} content={content} />
          }

          return (
            <Card
              key={i}
              className={`p-3 ${
                isUser ? "bg-blue-600 text-white border-blue-600" : "bg-white border-gray-200 shadow-sm"
              }`}
            >
              {isUser ? (
                <div className="whitespace-pre-wrap break-words">{content}</div>
              ) : (
                <MarkdownRenderer content={content} />
              )}
            </Card>
          )
        })}

        <div className={`text-xs text-gray-500 mt-1 ${isUser ? "text-right" : "text-left"}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {isUser && (
        <Avatar className="w-8 h-8 mt-1">
          <AvatarFallback className="bg-gray-100 text-gray-600">
            <User className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
