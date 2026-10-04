import noJsxComments from './rules/no-jsx-comments.js'
import noLiteralCopy from './rules/no-literal-copy.js'

/** This project's own rules, for the conventions no published plugin expresses. */
export default {
  meta: { name: 'local' },
  rules: {
    'no-jsx-comments': noJsxComments,
    'no-literal-copy': noLiteralCopy,
  },
}
