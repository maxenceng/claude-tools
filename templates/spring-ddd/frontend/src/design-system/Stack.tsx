import type { JSX, ReactNode } from 'react'
import styles from './Stack.module.css'

export type Space = 'none' | 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface StackProps {
  children: ReactNode
  /** Distance between children, from the spacing scale. */
  gap: Space
  direction?: 'vertical' | 'horizontal'
  align?: 'stretch' | 'start' | 'center' | 'baseline'
}

/** Lays its children out in a line, spaced by a token rather than by margins on each child. */
export function Stack({ children, gap, direction = 'vertical', align = 'stretch' }: StackProps): JSX.Element {
  return (
    <div className={styles.stack} data-gap={gap} data-direction={direction} data-align={align}>
      {children}
    </div>
  )
}
