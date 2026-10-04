const STATIC_TEXT = /\S/

/**
 * The string literals an expression can evaluate to, through the forms copy hides in:
 * `a ? 'x' : t('y')`, `detail ?? 'x'`, `'x' as string`, `` `x ${n}` `` and `'x' + n`.
 * A call is never entered, so `t('popularity.heading')` is a key, not copy.
 */
export function copyLiterals(node) {
  switch (node.type) {
    case 'Literal':
      return typeof node.value === 'string' && STATIC_TEXT.test(node.value) ? [node] : []
    case 'TemplateLiteral':
      return node.quasis.some((quasi) => STATIC_TEXT.test(quasi.value.cooked ?? quasi.value.raw)) ? [node] : []
    case 'ConditionalExpression':
      return [...copyLiterals(node.consequent), ...copyLiterals(node.alternate)]
    case 'LogicalExpression':
      return [...copyLiterals(node.left), ...copyLiterals(node.right)]
    case 'BinaryExpression':
      return node.operator === '+' ? [...copyLiterals(node.left), ...copyLiterals(node.right)] : []
    case 'TSAsExpression':
    case 'TSSatisfiesExpression':
    case 'TSNonNullExpression':
      return copyLiterals(node.expression)
    default:
      return []
  }
}

export function isStaticText(text) {
  return STATIC_TEXT.test(text)
}
