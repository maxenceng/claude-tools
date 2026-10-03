import type { JSX, ReactNode } from 'react'
import styles from './Heading.module.css'

export interface HeadingProps {
  children: ReactNode
  /** The document-outline level; the size follows it. */
  level: 1 | 2 | 3
  /** For a landmark that names itself by this heading (`aria-labelledby`). */
  id?: string
}

export function Heading({ children, level, id }: HeadingProps): JSX.Element {
  const Tag = `h${level}` as const
  return (
    <Tag id={id} className={styles.heading}>
      {children}
    </Tag>
  )
}
