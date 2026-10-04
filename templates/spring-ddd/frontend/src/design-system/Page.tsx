import type { JSX, ReactNode } from 'react'
import styles from './Page.module.css'

export interface PageProps {
  children: ReactNode
}

/** The page's `<main>` landmark, at a readable width. */
export function Page({ children }: PageProps): JSX.Element {
  return <main className={styles.page}>{children}</main>
}
