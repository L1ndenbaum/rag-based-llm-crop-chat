"use client"

import Image from "next/image" // 👈 添加 Image 引入
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Card } from "@/components/ui/card"
import { Bot, User } from "lucide-react"
import { MarkdownRenderer } from "./markdown-renderer"
import { ThinkingSection } from "./thinking-section"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: string
  isStreaming?: boolean
  images?: string[] // 添加图片字段
}

interface MessageBubbleProps {
  message: Message
  isLoading?: boolean
}

interface ParsedContent {
  parts: Array<{
    type: "thinking" | "content"
    content: string
    isComplete?: boolean
  }>
}

export function MessageBubble({ message, isLoading }: MessageBubbleProps) {
  const isUser = message.role === "user"
  const isAssistant = !isUser
  const isStreaming = message.isStreaming || isLoading

  // 解析思考部分和正常内容（支持流式解析）
  const parseStreamContent = (content: string): ParsedContent => {
    const parts: ParsedContent["parts"] = []
    let currentIndex = 0
    let inThinking = false
    let thinkingContent = ""
    let normalContent = ""

    while (currentIndex < content.length) {
      const thinkStartIndex = content.indexOf("<think>", currentIndex)
      const thinkEndIndex = content.indexOf("</think>", currentIndex)

      if (!inThinking) {
        if (thinkStartIndex === -1) {
          normalContent += content.slice(currentIndex)
          break
        } else {
          normalContent += content.slice(currentIndex, thinkStartIndex)
          if (normalContent.trim()) {
            parts.push({ type: "content", content: normalContent.trim(), isComplete: true })
            normalContent = ""
          }
          inThinking = true
          currentIndex = thinkStartIndex + "<think>".length
        }
      } else {
        if (thinkEndIndex === -1) {
          thinkingContent += content.slice(currentIndex)
          parts.push({ type: "thinking", content: thinkingContent, isComplete: false })
          break
        } else {
          thinkingContent += content.slice(currentIndex, thinkEndIndex)
          parts.push({ type: "thinking", content: thinkingContent, isComplete: true })
          thinkingContent = ""
          inThinking = false
          currentIndex = thinkEndIndex + "</think>".length
        }
      }
    }

    if (normalContent.trim()) {
      parts.push({ type: "content", content: normalContent.trim(), isComplete: true })
    }

    return { parts }
  }

  const { parts } = isUser
    ? { parts: [{ type: "content" as const, content: message.content, isComplete: true }] }
    : parseStreamContent(message.content)

  return (
    <div
      className={`flex gap-3 animate-in slide-in-from-bottom-2 duration-300 ${
        isUser ? "justify-end" : "justify-start"
      }`}
    >
      {isAssistant && (
        <Avatar className="w-8 h-8 mt-1 ring-2 ring-blue-100">
          <Image
            src="/images/corn-avatar.jpeg" // 👈 这就是 AI 头像
            alt="Assistant Avatar"
            width={32}
            height={32}
            unoptimized
            className="rounded-full"
          />
        </Avatar>
      )}

      <div className={`max-w-[85%] md:max-w-[70%] ${isUser ? "order-first" : ""}`}>
        {parts.map((part, index) => (
          <div key={index} className={part.type === "thinking" ? "mb-2" : ""}>
            {part.type === "thinking" ? (
              <ThinkingSection content={part.content} isStreaming={!part.isComplete && isStreaming} />
            ) : (
              part.content && (
                <Card
                  className={`p-4 transition-all duration-200 hover:shadow-md ${
                    isUser
                      ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white border-blue-600 shadow-lg"
                      : "bg-white border-gray-200 shadow-sm hover:shadow-md"
                  } mb-2`}
                >
                  {/* 用户消息显示图片 */}
                  {isUser && message.images && message.images.length > 0 && (
                    <div className="mb-3 flex flex-wrap gap-2">
                      {message.images.map((imageUrl, imgIndex) => (
                        <img
                          key={imgIndex}
                          src={imageUrl || "/placeholder.svg"}
                          alt={`Uploaded image ${imgIndex + 1}`}
                          className="max-w-full h-auto max-h-48 rounded-lg border border-white/20"
                        />
                      ))}
                    </div>
                  )}

                  {isUser ? (
                    <div className="whitespace-pre-wrap break-words">{part.content}</div>
                  ) : (
                    <div className="relative">
                      <MarkdownRenderer content={part.content} />
                      {!part.isComplete && isStreaming && (
                        <div className="inline-flex items-center ml-1">
                          <div className="w-2 h-4 bg-blue-500 animate-pulse rounded-sm"></div>
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              )
            )}
          </div>
        ))}

        {parts.length === 0 && isStreaming && (
          <Card className="p-4 bg-white border-gray-200 shadow-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-4 bg-blue-500 animate-pulse rounded-sm"></div>
              <span className="text-sm text-gray-500">AI 正在思考...</span>
            </div>
          </Card>
        )}

        <div className={`text-xs text-gray-500 mt-2 ${isUser ? "text-right" : "text-left"}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
          {isStreaming && !isUser && <span className="ml-2 text-blue-500 animate-pulse">正在输入...</span>}
        </div>
      </div>

      {isUser && (
        <Avatar className="w-8 h-8 mt-1 ring-2 ring-blue-100">
          <AvatarFallback className="bg-gradient-to-br from-gray-500 to-gray-600 text-white">
            <User className="w-4 h-4" />
          </AvatarFallback>
        </Avatar>
      )}
    </div>
  )
}
