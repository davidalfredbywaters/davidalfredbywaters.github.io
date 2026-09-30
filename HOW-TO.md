# Your website: how it works

Everything that makes up your site is in this folder:

| Folder / file | What it holds |
|---|---|
| `content/blog/` | One text file per blog post |
| `content/pages/` | One text file per page (About, FAQ, the indexes, the online crossword pages) |
| `static/images/` | Pictures |
| `static/s/` | Downloadable files (PDF and .puz). Their web addresses are the same as on Squarespace. |
| `config.yaml` | Site settings: title, menu, title font, Donate link, Subscribe form |
| `templates/`, `static/css/` | The page design (you won't normally need to touch these) |
| `build.py` | The small program that turns the text files into web pages |

## Writing a post

Make a new file in `content/blog/`, for example `crossword-366-something.md`:

```
---
title: "Crossword 366: Something"
date: 2026-10-10 06:01
categories: [Crosswords]
---

![George Smith, Obliging the Company](/images/George-Smith-Obliging-the-Company.jpg "George Smith, Obliging the Company")

***

*This week's introduction, in italics.*

***

***Download this fortnight's crossword:***

[366-Something.puz](/s/366-Something.puz)

[366-Something.pdf](/s/366-Something.pdf)

***Solve this fortnight's crossword online:***

[366: Something](/366-something)
```

- The part between the `---` lines is the header. Its **date** decides when the post appears. A future date means the post stays hidden until that morning, just like Squarespace's scheduling.
- `![caption](/images/file.jpg "caption")` shows a picture with a caption underneath. Put the picture file in `static/images/`.
- `***` on its own line draws a thin horizontal rule.
- `*italic*`, `**bold**` and `[link text](address)` work as usual.
- Put the .puz and .pdf files in `static/s/`.
- Its web address is made automatically: `/blog/2026/10/10/crossword-366-something`.

## Adding an online crossword page

Copy any file in `content/pages/` whose name ends in `-online` (for example `290-alternate-endings-online.md`), rename it, and change three things: the title, the `url:` line, and the `data-id="..."` value in the embed code, which is the puzzle ID PuzzleMe gives you.

## Publishing

When your site is on GitHub, saving a change publishes it within about a minute. The site also rebuilds every morning so that scheduled posts appear on their date.

To preview on your Mac first, open Terminal in this folder and run:

```
pip3 install -r requirements.txt     # first time only
python3 build.py --serve
```

Then visit http://localhost:8000.
