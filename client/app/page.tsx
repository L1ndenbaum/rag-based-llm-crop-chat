"use client"

import type React from "react"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { MessageSquare, Send, Plus, X } from "lucide-react"
import { MessageBubble } from "@/components/message-bubble"
import { ConversationList } from "@/components/conversation-list"
import { ImageUpload } from "@/components/image-upload"
import { AuthGuard } from "@/components/auth-guard"
import { UserMenu } from "@/components/user-menu"

interface Message {
  role: "user" | "assistant"
  content: string
  timestamp: string
  isStreaming?: boolean
}

interface Conversation {
  id: string
  name: string
  created_at: string
  updated_at: string
}

interface UploadedFile {
  file: File
  fileId: string
  preview: string
}

export default function ChatbotPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null)
  const [currentConversationName, setCurrentConversationName] = useState<string>("")
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [showSidebar, setShowSidebar] = useState(true)
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [username, setUsername] = useState<string>("")
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const abortControllerRef = useRef<AbortController | null>(null)

  const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8080"

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    // 获取用户名
    const storedUsername = localStorage.getItem("username")
    if (storedUsername) {
      setUsername(storedUsername)
    }
    loadConversations(storedUsername)
  }, [])

  const loadConversations = async (username: string|null) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/list/${username}`)
      const data = await response.json()
      setConversations(data.conversations || [])
    } catch (error) {
      console.error("Failed to load conversations:", error)
    }
  }

  const loadConversation = async (conversationId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`)
      const data = await response.json()
      setMessages(data.conversation.messages || [])
      setCurrentConversationId(conversationId)

      // 从对话列表中找到对话名称
      const conversation = conversations.find((conv) => conv.id === conversationId)
      setCurrentConversationName(conversation?.name || "对话")
    } catch (error) {
      console.error("Failed to load conversation:", error)
    }
  }

  const deleteConversation = async (conversationId: string) => {
    try {
      await fetch(`${API_BASE_URL}/api/conversations/${conversationId}`, {
        method: "DELETE",
      })
      setConversations((prev) => prev.filter((conv) => conv.id !== conversationId))
      if (currentConversationId === conversationId) {
        setMessages([])
        setCurrentConversationId(null)
        setCurrentConversationName("")
      }
    } catch (error) {
      console.error("Failed to delete conversation:", error)
    }
  }

  const startNewConversation = () => {
    setMessages([])
    setCurrentConversationId(null)
    setCurrentConversationName("")
    setUploadedFiles([])
  }

  const handleFileUpload = (files: File[], fileIds: string[]) => {
    const newFiles: UploadedFile[] = files.map((file, index) => ({
      file,
      fileId: fileIds[index] || "",
      preview: URL.createObjectURL(file),
    }))

    setUploadedFiles((prev) => [...prev, ...newFiles])
  }

  const removeFile = (index: number) => {
    setUploadedFiles((prev) => {
      const newFiles = [...prev]
      URL.revokeObjectURL(newFiles[index].preview)
      newFiles.splice(index, 1)
      return newFiles
    })
  }

  const sendMessage = async () => {
    if (!input.trim() && uploadedFiles.length === 0) return

    const userMessage: Message = {
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    const currentFiles = uploadedFiles
    setInput("")
    setUploadedFiles([])
    setIsLoading(true)

    const assistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    }

    setMessages((prev) => [...prev, assistantMessage])
    abortControllerRef.current = new AbortController()

    try {
      // 添加用户名字段到请求数据
      const requestData = {
        message: currentInput,
        conversation_id: currentConversationId,
        file_ids: currentFiles.map((f) => f.fileId).filter((id) => id),
        username: username, // 添加用户名字段
      }

      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestData),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      if (!response.body) {
        throw new Error("Response body is null")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let accumulatedContent = ""

      try {
        while (true) {
          const { done, value } = await reader.read()

          if (done) {
            break
          }

          const chunk = decoder.decode(value, { stream: true })

          if (chunk.startsWith("[ERROR]")) {
            setMessages((prev) =>
              prev.map((msg, index) =>
                index === prev.length - 1
                  ? {
                      ...msg,
                      content: chunk,
                      isStreaming: false,
                    }
                  : msg,
              ),
            )
            break
          }

          accumulatedContent += chunk

          setMessages((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1
                ? {
                    ...msg,
                    content: accumulatedContent,
                    isStreaming: true,
                  }
                : msg,
            ),
          )
        }

        setMessages((prev) =>
          prev.map((msg, index) =>
            index === prev.length - 1
              ? {
                  ...msg,
                  isStreaming: false,
                }
              : msg,
          ),
        )

        currentFiles.forEach((file) => {
          URL.revokeObjectURL(file.preview)
        })

        await loadConversations(username)

        if (!currentConversationId) {
          const updatedConversations = await fetch(`${API_BASE_URL}/api/conversations`).then((r) => r.json())
          if (updatedConversations.conversations && updatedConversations.conversations.length > 0) {
            const latestConv = updatedConversations.conversations[0]
            setCurrentConversationId(latestConv.id)
            setCurrentConversationName(latestConv.name)
          }
        }
      } catch (streamError) {
        if (streamError instanceof Error && streamError.name === "AbortError") {
          console.log("Request was aborted")
        } else {
          console.error("Stream reading error:", streamError)
          setMessages((prev) =>
            prev.map((msg, index) =>
              index === prev.length - 1
                ? {
                    ...msg,
                    content: "流式传输出现错误，请重试。",
                    isStreaming: false,
                  }
                : msg,
            ),
          )
        }
      }
    } catch (error) {
      console.error("Failed to send message:", error)
      setMessages((prev) =>
        prev.map((msg, index) =>
          index === prev.length - 1
            ? {
                ...msg,
                content: "发送消息失败，请检查网络连接后重试。",
                isStreaming: false,
              }
            : msg,
        ),
      )
    } finally {
      setIsLoading(false)
      abortControllerRef.current = null
    }
  }

  const stopGeneration = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      if (isLoading) {
        stopGeneration()
      } else {
        sendMessage()
      }
    }
  }

  return (
    <AuthGuard>
      <div className="flex h-screen bg-gray-50">
        {/* 侧边栏 */}
        {showSidebar && (
          <div className="w-80 bg-white border-r border-gray-200 flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <Button
                onClick={startNewConversation}
                className="w-full justify-start gap-2 bg-transparent"
                variant="outline"
              >
                <Plus className="w-4 h-4" />
                新建对话
              </Button>
            </div>

            <ConversationList
              conversations={conversations}
              currentConversationId={currentConversationId}
              onSelectConversation={loadConversation}
              onDeleteConversation={deleteConversation}
            />
          </div>
        )}

        {/* 主聊天区域 */}
        <div className="flex-1 flex flex-col">
          {/* 头部 */}
          <div className="bg-white border-b border-gray-200 p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Button variant="ghost" size="sm" onClick={() => setShowSidebar(!showSidebar)}>
                <MessageSquare className="w-4 h-4" />
              </Button>
              <h1 className="text-lg font-semibold">{currentConversationName || "AI 助手"}</h1>
            </div>
            <div className="flex items-center gap-2">
              {isLoading && (
                <Button variant="outline" size="sm" onClick={stopGeneration}>
                  停止生成
                </Button>
              )}
              <UserMenu />
            </div>
          </div>

          {/* 消息区域 */}
          <ScrollArea className="flex-1 p-4">
            <div className="max-w-4xl mx-auto space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 mt-20">
                  <MessageSquare className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p className="text-lg mb-2">开始与玉米知识问答助手对话</p>
                  <p className="text-sm">发送消息开始聊天😀，支持 Markdown 格式、思考过程展示和图片上传</p>
                </div>
              ) : (
                messages.map((message, index) => (
                  <MessageBubble key={index} message={message} isLoading={message.isStreaming} />
                ))
              )}
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* 输入区域 */}
          <div className="bg-white border-t border-gray-200 p-4">
            <div className="max-w-4xl mx-auto">
              {/* 文件预览 */}
              {uploadedFiles.length > 0 && (
                <div className="mb-3 flex flex-wrap gap-2">
                  {uploadedFiles.map((uploadedFile, index) => (
                    <div key={index} className="relative group">
                      <img
                        src={uploadedFile.preview || "/placeholder.svg"}
                        alt={`Upload ${index + 1}`}
                        className="w-16 h-16 object-cover rounded-lg border"
                      />
                      {!uploadedFile.fileId && (
                        <div className="absolute inset-0 bg-red-500 bg-opacity-20 rounded-lg flex items-center justify-center">
                          <span className="text-xs text-red-600 font-medium">上传失败</span>
                        </div>
                      )}
                      <Button
                        size="sm"
                        variant="destructive"
                        className="absolute -top-2 -right-2 w-5 h-5 rounded-full p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => removeFile(index)}
                      >
                        <X className="w-3 h-3" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}

              <div className="flex items-end gap-2">
                <div className="flex-1 relative">
                  <Input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isLoading ? "AI正在回复中... 按Enter停止" : "输入消息..."}
                    className="pr-20 min-h-[44px] resize-none"
                    disabled={false}
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    <ImageUpload onUpload={handleFileUpload} disabled={isLoading} />
                  </div>
                </div>
                <Button
                  onClick={isLoading ? stopGeneration : sendMessage}
                  disabled={!isLoading && !input.trim() && uploadedFiles.length === 0}
                  size="sm"
                  className="h-[44px] px-4"
                  variant={isLoading ? "destructive" : "default"}
                >
                  {isLoading ? "停止" : <Send className="w-4 h-4" />}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </AuthGuard>
  )
}
