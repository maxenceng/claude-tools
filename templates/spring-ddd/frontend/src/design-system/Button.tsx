import type { JSX, ReactNode } from 'react'
import styles from './Button.module.css'

export interface ButtonProps {
  children: ReactNode
  /** Required, so no button submits a form by accident. */
  type: 'button' | 'submit'
  /** `link` is a secondary action that reads as text, such as Retry inside an Alert. */
  variant?: 'primary' | 'link'
  onClick?: () => void
}

export function Button({ children, type, variant = 'primary', onClick }: ButtonProps): JSX.Element {
  return (
    <button
      type={type === 'submit' ? 'submit' : 'button'}
      className={styles.button}
      data-variant={variant}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
