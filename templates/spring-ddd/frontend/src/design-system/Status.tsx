import type { JSX, ReactNode } from 'react'
import styles from './Status.module.css'

export interface StatusProps {
  children: ReactNode
}

/** Transient progress, such as a lookup in flight; announced politely. */
export function Status({ children }: StatusProps): JSX.Element {
  return (
    <p role="status" className={styles.status}>
      {children}
    </p>
  )
}
