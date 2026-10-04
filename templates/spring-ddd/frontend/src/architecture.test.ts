import { readdirSync, readFileSync } from 'node:fs'
import path from 'node:path'
import { describe, expect, it } from 'vitest'

const src = import.meta.dirname
const api = path.join(src, 'api')
const generated = path.join(api, 'generated')
const designSystem = path.join(src, 'design-system')
const i18n = path.join(src, 'i18n')
const sharedFolders = new Set(['api', 'design-system', 'i18n', 'test']) // not bounded contexts

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
  const specifiers = [...text.matchAll(/(?:from\s+|import\s*\(\s*|import\s+)['"](?<specifier>[^'"]+)['"]/g)].map(
    (m) => m.groups?.specifier ?? '',
  )
  return specifiers.filter((s) => s.startsWith('.')).map((s) => path.resolve(path.dirname(file), s))
}

const within = (target: string, dir: string): boolean => target === dir || target.startsWith(dir + path.sep)
/** The top-level folder of src/ a path lives in; a file directly in src/ has none. */
const folderOf = (file: string): string => {
  const parts = path.relative(src, file).split(path.sep)
  return parts.length > 1 ? (parts[0] ?? '') : ''
}
/** A bounded context: a top-level folder of src/ that is not shared. */
const isContext = (folder: string): boolean => folder !== '' && !sharedFolders.has(folder)
const show = (file: string, target: string): string => `${path.relative(src, file)} → ${path.relative(src, target)}`

function violations(offends: (file: string, target: string) => boolean): string[] {
  return sourceFiles(src).flatMap((file) =>
    relativeImports(file)
      .filter((target) => offends(file, target))
      .map((target) => show(file, target)),
  )
}

describe('frontend architecture', () => {
  it('scans source files, so the rules below cannot pass on an empty list', () => {
    expect(sourceFiles(src)).not.toEqual([])
  })

  it('a bounded context never imports from another bounded context', () => {
    const found = violations((file, target) => {
      const own = folderOf(file)
      const other = folderOf(target)
      return isContext(own) && isContext(other) && other !== own
    })

    expect(found).toEqual([])
  })

  it('only src/api imports from the generated client', () => {
    const found = violations(
      (file, target) => within(target, generated) && !within(file, api),
    )

    expect(found).toEqual([])
  })

  it('the design system imports no bounded context', () => {
    const found = violations((file, target) => within(file, designSystem) && isContext(folderOf(target)))

    expect(found).toEqual([])
  })

  it('the design system does not talk to the API', () => {
    const found = violations((file, target) => within(file, designSystem) && within(target, api))

    expect(found).toEqual([])
  })

  it('i18n imports no bounded context', () => {
    const found = violations((file, target) => within(file, i18n) && isContext(folderOf(target)))

    expect(found).toEqual([])
  })
})
