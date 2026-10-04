<h1 align="center">skills</h1>

<p align="center">Skills for me (and you)</p>

<br />

## Introduction

Agent skills I use across my own projects, written down so an agent (or you) can pick them up.
Opinionated by design.

> [!WARNING]
> Built for me, shared in the open.
>
> No support, no guarantees, no liability — read a skill before you install it.

## Install

```sh
npx skills@latest add joe-bell/skills
```

### Individual skills

```sh
npx skills@latest add joe-bell/skills --skill apple-web-app
```

### `.zip`

Apps such as Claude and ChatGPT install a skill from an uploaded zip instead of
the command line. On macOS, this builds one in the current folder; set `s` to
the skill's name:

```sh
s=apple-web-app; curl -fsSo /dev/null https://raw.githubusercontent.com/joe-bell/skills/main/skills/$s/SKILL.md && curl -fsSL https://github.com/joe-bell/skills/archive/main.tar.gz | tar -cf $s.zip --format zip --include "*/skills/$s/*" -s "|^[^/]*/skills/||" @-
```

Then upload `apple-web-app.zip` in the app's skill settings.

## Reference

- [**apple-web-app**](./skills/apple-web-app/SKILL.md) — Building websites and web apps that work well on iOS, iPadOS and macOS Safari
- [**elron**](./skills/elron/SKILL.md) — Checking Estonian train times, live delays and Elron farecard balances
- [**letterboxd-diary**](./skills/letterboxd-diary/SKILL.md) — Fetching recently watched films from a Letterboxd diary

## License

[MIT](/LICENSE) © [Joe Bell](https://joebell.studio)
