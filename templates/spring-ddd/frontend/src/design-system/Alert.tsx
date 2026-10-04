import type { JSX, ReactNode } from 'react'
import styles from './Alert.module.css'

export interface AlertProps {
  children: ReactNode
}

/** A failure the person must notice now; announced as soon as it appears. */
export function Alert({ children }: AlertProps): JSX.Element {
  return (
    <div role="alert" className={styles.alert}>
      {children}
    </div>
  )
}
