# Detecting the formatting setup

Read the setup before reordering anything. Two minutes here avoids a diff that
the project's own formatter immediately undoes.

## Is Prettier configured?

Look for `.prettierrc` and its variants, `prettier.config.*`, or a `prettier`
key in `package.json`. Resolution is per file from that file's directory
upwards, so a monorepo package may override the root.

`printWidth` is the break target for the strings Prettier cannot reflow. When
no config sets it, use Prettier's default of `80`.

## Is prettier-plugin-tailwindcss installed?

Check `package.json` dependencies and the `plugins` array in the Prettier
config.

If it is installed, these apply:

- It sorts `class` and `className` attributes, and `@apply` directives, with
  no extra configuration.
- It sorts other attributes only when they are listed in
  `tailwindAttributes`.
- It sorts class helpers such as `cva`, `cx`, `clsx` and `cn` only when they
  are listed in `tailwindFunctions`. An unsorted helper is a project decision;
  do not add it to the config as part of tidying a class list.

The division of labour: the plugin orders classes **within** each string, and
`anorak-css` decides **which classes share** a string or line.

## Neither is present

Apply section 3's order directly and keep the file's existing conventions for
quoting, indentation and line breaks.

## Checking the split is safe

After editing, confirm the diff shows only moves and re-splits. In a class
helper, watch for:

- Duplicate properties whose resolution depends on order.
- Conditional segments, which must stay in their original position.
- A trailing consumer `className`, which must remain last.
