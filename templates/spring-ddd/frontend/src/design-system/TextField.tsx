import { useId, type ChangeEvent, type JSX } from 'react'
import styles from './TextField.module.css'

export interface TextFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  /** Why the value was refused; shown under the input and tied to it for assistive technology. */
  error?: string
}

/**
 * A labelled text input with its error slot.
 *
 * The slot is mounted even when empty: a live region announces only changes that happen
 * after it exists, and an error must be heard wherever focus is — on the field after a
 * submit by Enter, on the button after a click.
 */
export function TextField({ label, value, onChange, error }: TextFieldProps): JSX.Element {
  const inputId = useId()
  const errorId = useId()
  const invalid = error !== undefined && error !== ''

  function change(event: ChangeEvent<HTMLInputElement>): void {
    onChange(event.target.value)
  }

  return (
    <div className={styles.field}>
      <label htmlFor={inputId} className={styles.label}>
        {label}
      </label>
      <input
        id={inputId}
        className={styles.input}
        value={value}
        onChange={change}
        aria-invalid={invalid ? true : undefined}
        aria-describedby={invalid ? errorId : undefined}
      />
      <p id={errorId} className={styles.error} aria-live="polite">
        {error}
      </p>
    </div>
  )
}
