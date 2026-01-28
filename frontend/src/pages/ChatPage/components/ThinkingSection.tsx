import React, { useState } from 'react';
import { CaretRightOutlined, BulbOutlined } from '@ant-design/icons';
import { theme } from 'antd';
import { motion, AnimatePresence } from 'framer-motion';
import { MarkdownRenderer } from '../../../components/MarkdownRenderer';
import { accordion } from '../../../utils/animations';
import styles from './ThinkingSection.module.css';

interface ThinkingSectionProps {
  content: string;
  isStreaming?: boolean;
}

const ThinkingSection: React.FC<ThinkingSectionProps> = ({ content, isStreaming }) => {
  const [expanded, setExpanded] = useState(true);
  const { token } = theme.useToken();

  // 当正在流式传输且有内容时，自动展开（可选，或者保持用户选择）
  // 这里我们选择：如果开始流式传输，且本来没有内容，则展开。
  // 如果用户手动折叠了，就不自动展开。
  
  if (!content) return null;

  return (
    <div 
      className={styles.container} 
      style={{ 
        borderColor: token.colorBorderSecondary,
        backgroundColor: token.colorFillQuaternary 
      }}
    >
      <div 
        className={styles.header} 
        onClick={() => setExpanded(!expanded)}
        style={{ color: token.colorTextSecondary }}
      >
        <div className={styles.title}>
          <BulbOutlined />
          <span>Thinking Process</span>
          {isStreaming && <span className={styles.dot} />}
        </div>
        <CaretRightOutlined rotate={expanded ? 90 : 0} style={{ transition: 'transform 0.2s' }} />
      </div>
      <AnimatePresence initial={false}>
        {expanded && (
          <motion.div
            key="content"
            initial="initial"
            animate="animate"
            exit="exit"
            variants={accordion}
            style={{ overflow: 'hidden' }}
          >
            <div 
              className={styles.content} 
              style={{ 
                color: token.colorTextTertiary,
                borderTopColor: token.colorBorderSecondary
              }}
            >
              <MarkdownRenderer content={content} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};


export default ThinkingSection;
