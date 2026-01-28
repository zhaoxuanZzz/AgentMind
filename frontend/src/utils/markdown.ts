/**
 * Markdown 处理工具
 */

/**
 * 清理 Markdown 文本
 * - 移除多余的空行
 * - 统一换行符
 */
export function cleanMarkdown(text: string): string {
  return text
    .replace(/\r\n/g, '\n') // 统一换行符
    .replace(/\n{3,}/g, '\n\n') // 最多保留两个连续换行
    .trim()
}

/**
 * 提取 Markdown 中的代码块
 */
export function extractCodeBlocks(markdown: string): Array<{
  language: string
  code: string
  raw: string
}> {
  const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g
  const blocks: Array<{ language: string; code: string; raw: string }> = []

  let match
  while ((match = codeBlockRegex.exec(markdown)) !== null) {
    blocks.push({
      language: match[1] || 'plaintext',
      code: match[2].trim(),
      raw: match[0],
    })
  }

  return blocks
}

/**
 * 检测文本是否包含 Markdown 语法
 */
export function hasMarkdownSyntax(text: string): boolean {
  const patterns = [
    /^#+\s/m,           // 标题
    /\*\*.*\*\*/,       // 粗体
    /\*.*\*/,           // 斜体
    /\[.*\]\(.*\)/,     // 链接
    /```/,              // 代码块
    /`.*`/,             // 行内代码
    /^[-*+]\s/m,        // 列表
    /^\d+\.\s/m,        // 有序列表
    /^>\s/m,            // 引用
  ]

  return patterns.some(pattern => pattern.test(text))
}

/**
 * 截断文本并添加省略号
 */
export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text
  }
  return text.slice(0, maxLength) + '...'
}

/**
 * 高亮搜索关键词
 */
export function highlightKeywords(
  text: string,
  keywords: string[],
  className = 'highlight'
): string {
  if (!keywords.length) return text

  let result = text
  keywords.forEach(keyword => {
    const regex = new RegExp(`(${escapeRegExp(keyword)})`, 'gi')
    result = result.replace(regex, `<span class="${className}">$1</span>`)
  })

  return result
}

/**
 * 转义正则表达式特殊字符
 */
function escapeRegExp(string: string): string {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/**
 * 将 Markdown 转换为纯文本（移除所有格式）
 */
export function markdownToPlainText(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, '') // 移除代码块
    .replace(/`[^`]+`/g, '') // 移除行内代码
    .replace(/!\[.*?\]\(.*?\)/g, '') // 移除图片
    .replace(/\[([^\]]+)\]\(.*?\)/g, '$1') // 保留链接文本
    .replace(/^#+\s+/gm, '') // 移除标题标记
    .replace(/(\*\*|__)(.*?)\1/g, '$2') // 移除粗体标记
    .replace(/(\*|_)(.*?)\1/g, '$2') // 移除斜体标记
    .replace(/^[-*+]\s+/gm, '') // 移除列表标记
    .replace(/^\d+\.\s+/gm, '') // 移除有序列表标记
    .replace(/^>\s+/gm, '') // 移除引用标记
    .trim()
}
