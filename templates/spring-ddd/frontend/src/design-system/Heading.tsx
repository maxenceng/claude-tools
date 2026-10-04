import type { JSX, ReactNode } from 'react'
import styles from './Heading.module.css'

export interface HeadingProps {
  children: ReactNode
  /** The document-outline level; the size follows it. */
  level: 1 | 2 | 3
  /** For a landmark that names itself by this heading (`aria-labelledby`). */
  id?: string
}

const TAGS: Record<HeadingProps['level'], 'h1' | 'h2' | 'h3'> = { 1: 'h1', 2: 'h2', 3: 'h3' }

export function Heading({ children, level, id }: HeadingProps): JSX.Element {
  const Tag = TAGS[level]
  return (
    <Tag id={id} className={styles.heading}>
      {children}
    </Tag>
  )
}
