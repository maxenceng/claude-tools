import ts from 'typescript'
import { copyLiterals, isStaticText } from './copy-literals.js'

/** The attributes of an HTML element a person reads or hears; the rest are tokens and ids. */
const HUMAN_READABLE_ATTRIBUTES = new Set([
  'alt',
  'title',
  'placeholder',
  'label',
  'aria-label',
  'aria-description',
  'aria-roledescription',
  'aria-valuetext',
  'aria-placeholder',
])

/** React reads `key` itself and never renders it, whatever its declared type. */
const REACT_RESERVED_PROPS = new Set(['key'])

function isIntrinsic(openingElement) {
  return openingElement.name.type === 'JSXIdentifier' && /^[a-z]/.test(openingElement.name.name)
}

function attributeName(attribute) {
  return attribute.name.type === 'JSXIdentifier'
    ? attribute.name.name
    : `${attribute.name.namespace.name}:${attribute.name.name.name}`
}

/** @type {import('eslint').Rule.RuleModule} */
export default {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Copy rendered as JSX text, in a human-readable HTML attribute, or in a component prop typed to take free text, comes from i18n.',
    },
    schema: [],
    messages: {
      copy: 'User-facing text comes from i18n: render t(…) instead of a string literal.',
      copyInProp:
        'This prop is typed to take free text, so a string literal here reads as copy: render t(…) for text a person reads; for an id or a path, narrow the prop to a literal union, or pass a module-scope constant or useId().',
    },
  },
  create(context) {
    const services = context.sourceCode.parserServices
    const program = services?.program
    const checker = program?.getTypeChecker()

    function report(nodes, messageId = 'copy') {
      for (const node of nodes) context.report({ node, messageId })
    }

    /** Whether the prop this value is passed to is declared as free text: `string`, `ReactNode`, or a union holding one. */
    function takesFreeText(expression) {
      if (!checker) return false
      const type = checker.getContextualType(services.esTreeNodeToTSNodeMap.get(expression))
      if (!type) return false
      const constituents = type.isUnion() ? type.types : [type]
      return constituents.some((constituent) => (constituent.flags & ts.TypeFlags.String) !== 0)
    }

    return {
      JSXText(node) {
        if (isStaticText(node.value)) report([node])
      },
      JSXExpressionContainer(node) {
        if (node.parent.type === 'JSXAttribute' || node.expression.type === 'JSXEmptyExpression') return
        report(copyLiterals(node.expression))
      },
      JSXAttribute(node) {
        if (node.value === null) return
        const expression = node.value.type === 'JSXExpressionContainer' ? node.value.expression : node.value
        if (expression.type === 'JSXEmptyExpression') return
        const name = attributeName(node)
        if (isIntrinsic(node.parent)) {
          if (HUMAN_READABLE_ATTRIBUTES.has(name)) report(copyLiterals(expression))
        } else if (!REACT_RESERVED_PROPS.has(name) && takesFreeText(expression)) {
          report(copyLiterals(expression), 'copyInProp')
        }
      },
    }
  },
}
