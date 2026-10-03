import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const src = import.meta.dirname
const generated = path.join(src, 'api', 'generated')
const sharedFolders = new Set(['api', 'test']) // not bounded contexts

function sourceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const full = path.join(dir, entry.name)
    if (full === generated) return []
    if (entry.isDirectory()) return sourceFiles(full)
    return /\.tsx?$/.test(entry.name) ? [full] : []
  })
}

/** Relative imports of a file, resolved to absolute paths. */
function relativeImports(file: string): string[] {
  const text = readFileSync(file, 'utf8')
  const specifiers = [...text.matchAll(/(?:from\s+|import\s*\(\s*|import\s+)['"]([^'"]+)['"]/g)].map((m) => m[1] ?? '')
  return specifiers.filter((s) => s.startsWith('.')).map((s) => path.resolve(path.dirname(file), s))
}

const within = (target: string, dir: string) => target === dir || target.startsWith(dir + path.sep)
/** The top-level folder of src/ a path lives in; a file directly in src/ has none. */
const folderOf = (file: string) => {
  const parts = path.relative(src, file).split(path.sep)
  return parts.length > 1 ? (parts[0] ?? '') : ''
}
const show = (file: string, target: string) => `${path.relative(src, file)} → ${path.relative(src, target)}`

function violations(offends: (file: string, target: string) => boolean): string[] {
  return sourceFiles(src).flatMap((file) =>
    relativeImports(file)
      .filter((target) => offends(file, target))
      .map((target) => show(file, target)),
  )
}

describe('frontend architecture', () => {
  it('a bounded context never imports from another bounded context', () => {
    const found = violations((file, target) => {
      const own = folderOf(file)
      const other = folderOf(target)
      return !sharedFolders.has(own) && own !== '' && other !== '' && other !== own && !sharedFolders.has(other)
    })

    expect(found).toEqual([])
  })

  it('only src/api imports from the generated client', () => {
    const found = violations(
      (file, target) => within(target, generated) && !within(file, path.join(src, 'api')),
    )

    expect(found).toEqual([])
  })
})
