function isInsideJsx(node) {
  for (let current = node; current; current = current.parent) {
    if (current.type === 'JSXElement' || current.type === 'JSXFragment') return true
  }
  return false
}

/** @type {import('eslint').Rule.RuleModule} */
export default {
  meta: {
    type: 'suggestion',
    docs: { description: 'No comment anywhere inside JSX, and no empty `{}` left behind.' },
    schema: [],
    messages: {
      comment: 'No comments inside JSX — explain above the component instead.',
      empty: 'Empty expression in JSX: remove the `{}`.',
    },
  },
  create(context) {
    const { sourceCode } = context
    return {
      'Program:exit'() {
        for (const comment of sourceCode.getAllComments()) {
          if (isInsideJsx(sourceCode.getNodeByRangeIndex(comment.range[0]))) {
            context.report({ loc: comment.loc, messageId: 'comment' })
          }
        }
      },
      'JSXExpressionContainer > JSXEmptyExpression'(node) {
        if (sourceCode.getCommentsInside(node.parent).length === 0) {
          context.report({ node: node.parent, messageId: 'empty' })
        }
      },
    }
  },
}
