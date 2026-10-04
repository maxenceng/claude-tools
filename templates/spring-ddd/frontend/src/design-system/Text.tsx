import type { JSX, ReactNode } from 'react'
import styles from './Text.module.css'

export interface TextProps {
  children: ReactNode
  /** `default` inherits the surrounding colour, so text inside an Alert takes its tone. */
  tone?: 'default' | 'muted'
  /** Inherits the surrounding size when omitted; `display` is for a single figure that is the point of the screen. */
  size?: 'sm' | 'md' | 'display'
  /** `span` for text that sits inline beside other text. */
  as?: 'p' | 'span'
}

export function Text({ children, tone = 'default', size, as: Tag = 'p' }: TextProps): JSX.Element {
  return (
    <Tag className={styles.text} data-tone={tone} data-size={size}>
      {children}
    </Tag>
  )
}
