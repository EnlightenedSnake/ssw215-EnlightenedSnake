# SPEC: Developer Portfolio Welcome Page

## 1. Purpose & Scope
- A personal portfolio welcome page for Jake Mikruk, a first-year software
engineering student.
- Non-Goals: no multi-page routing; no backend; no contact forms.

## 2. Invariants & Negative Constraints
- All styling MUST reside in `./style.css` (no inline style="..." attributes).
- The page MUST NOT load external CSS frameworks or CDNs (no Bootstrap, no Tailwind).
- The avatar image MUST use the relative path `./assets/avatar.png`.
- The layout MUST collapse into a single vertical column on screens narrower than 768px.
- style.css MUST begin with the universal reset: `*, *::before, *::after { box-sizing:
border-box; }`.
- Spacing and font sizes MUST use rem. px MAY be used only for borders.
- Styling MUST use class selectors. ID selectors MUST NOT be used for styling.

## 3. UI Content & Interface Contract
- Hero header: my full name "Jake Mikruk", the subtitle "I am a software engineering undergraduate studying at Stevens Institute of Technology.", and
this bio: "I am excited to learn more about current software engineering practices along with growing my capabilities as a software engineer. Alongside, I am a avid fan of tennis, skiing, running, and of course coding.".
- Action link: a button labelled "See my projects" that links to `#projects`.
- Projects section with id="projects": lists these items: A 3D game that uses only built in frontend commands, A RPG style game with selfmade graphics, A game that utilizes a backend to allow for smoother gameplay.
- Social link: GitHub (https://github.com/EnlightenedSnake) MUST open in a new tab (target="_blank").
- Headings MUST be underlined
- The page MUST use semantic landmarks: one <header>, one <nav>, one <main>, one <footer>, and each content group inside its own <section> with a heading.
- There MUST be exactly one <h1>, and heading levels MUST NOT skip (h1 then h2 then h3).
- <nav> MUST contain a link to the projects section and a link to my GitHub profile.
- Each project MUST be an <article class="card"> inside a container that uses display: flex, flex-wrap: wrap and gap.

## 4. Acceptance Checklist
- [ ] Exactly one <h1>, one <header>, one <nav>, one <main>, one <footer>.
- [ ] Every project is an <article class="card"> inside a flex container with gap.
- [ ] style.css begins with the box-sizing reset.
- [ ] No inline style="..." attributes anywhere in index.html.
- [ ] No ID selectors (#something) in style.css.
- [ ] No horizontal scrollbar when the browser is narrowed to 375px.

## 5. Audit Protocol
- Inspect the generated code line by line with `git diff --staged` before committing.