# Data display

How a screen shows figures, changes, tables and statuses. A generated screen falls into the
same handful of habits every time; each rule below names the habit it replaces. Every visual
value still comes from a token and every element from a primitive — when a rule needs a
look the design system does not have yet (tabular figures, a muted dash, a pale status
tint), add it there first.

## Figures

- **The answer leads.** When one figure answers the screen's question (its *Design
  direction* names it), it is the largest on the screen, clearly above its siblings. No
  other figure, in any region, is set larger.
- **Label above value**, the label smaller, muted and in sentence case; the unit a smaller,
  muted suffix ("5 min", "12.7k of 20.0k").
- **Sizes of a working screen**, not a landing page: a figure stays within the type scale's
  upper steps, never a display size.
- **No tile per figure by default.** Peer figures share one container split into equal
  columns; a figure that belongs to a region leads that region instead of repeating in a
  strip above it. One figure, one place.
- **Nothing decorative beside a figure**: no icon in a tinted circle or square, no sparkline,
  no gradient. A trend gets its own chart or none.
- **Numbers the data really has.** Sample and test data use believable values whose totals
  add up from the rows; no "Acme", "John Doe", "User 1" or round vanity totals.

## Changes

- A change is optional. When shown, it is never larger than its label, and it names its
  window in words ("vs prior 30 days").
- **Colour says good or bad, not up or down.** Every metric has a good direction: latency,
  error rate, cost and churn improve when they fall. The negative token goes on a change in
  the bad direction; a change in the good direction takes the positive token or stays
  muted.
- **No signal on nothing.** A zero or undefined change is muted. From a zero base, write the
  amount and "(new)", never a percentage; with nothing to compare, a muted dash.

## Tables and lists

- **Numbers right-aligned in tabular figures**, fixed decimals per column, units muted.
  Text left-aligned.
- **Headers** a step smaller, muted, sentence case — never tracked capitals, never a filled
  header band.
- **Rows** separated by a faint rule or by space; no zebra striping.
- **One status mark per row**, one action where it is needed — not a checkbox, avatar,
  chip and menu on every row by reflex.
- **Status pills** are a pale tint with dark text of the same hue, small, inside the row;
  never saturated with white text, never above a heading.
- **Short lists are capped**: a handful of rows, the total, and a "View all", not
  pagination under five rows.
- **Red is a signal, not a texture**: at most one negative mark per row, on the fact that
  is actually failing or overdue.

## Colour on a working screen

- The accent marks the primary action, the current selection and the data that matters —
  not every button, tab and link.
- Charts take one hue per series and four hues at most on a screen; the rest is neutral.
- Rows that are fine stay neutral; colour lands only on the rows at risk.

## Signs of a generated dashboard

Read before `/ticket review` on a screen like this; each line is a habit and what replaces it.

| Habit | Instead |
| --- | --- |
| "Welcome back" greeting with an emoji over the content | A noun title naming the screen |
| Four figure cards, each with an icon in a tinted circle | One container split into columns, label over value |
| A green "+12.5%" pill on every figure | A change only where it matters, its window in words, muted at zero |
| A sparkline on every figure | The trend in its own chart, or nowhere |
| Figures at display size, bold, in the brand colour | Figures in ink, within the scale's upper steps |
| Smoothed gradient area chart with a dot on every point | A plain line, no fill, no markers |
| A legend for a single series | The series named in the chart's title |
| Zebra table under tracked-capital headers | Faint rules, muted sentence-case headers |
| Left-aligned numbers in proportional digits | Right-aligned tabular figures |
| Saturated status chips with white text | Pale tint, dark text of the same hue |
| The accent on every button, tab and nav item | The accent on data and the one primary action |
| Export, Share and a date picker clustered by the title | Actions only when they are real |
| Pagination under a short list | Capped rows, the total, "View all" |
| An equal four-up grid whatever the item count | A column count chosen by the item count |
| An illustration and "No data yet" in an empty chart | The axis drawn, one sentence in the frame |

A screen with every habit removed and nothing in their place is a tidy template. What fills
the space is the product: its own data at its real size, the question answered by the
biggest block.

Adapted from [taste-skill](https://github.com/Leonxlnx/taste-skill)'s
`references/app-screens.md` (MIT).
