# The World in One Day — 25 November 2026

[![make.fun](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/stfu-onad/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/stfu-onad/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125)

One newspaper front page that tries to hold a whole day of world
news in a single picture: Wednesday, 25 November 2026.

The day's lead story is at sea. Ukraine's president confirmed
that Ukrainian forces sank two Russian ships — a cargo vessel in
the Gulf of Finland and a warship off Benghazi in Libya — and
Moscow answered by calling the strikes terrorism. The picture in
the middle of the page shows that moment: a cargo ship burning
at dusk, a drone overhead, a warship going down far behind it.

Next to it, the climate talks fall apart. COP31 in Antalya ended
with no deal at all, after oil and gas producing countries blocked
any language about phasing out fossil fuels. Below that, the war
in the Gulf spreads: Houthi strikes hit the tallest tower in
Riyadh and wounded eleven people, while the rebels push on
towards Aden. And in Washington, Donald Trump presented Rudy
Giuliani with the Medal of Freedom.

A ticker runs along the foot of the page with the rest of the
day's news in short bursts: Sarkozy ordered to stand trial,
NATO jets heading for Poland, tankers struck in the Strait of
Hormuz, the Gaza death toll reaching 74,746, a new analysis
putting Russian losses at 700,000, and England beating Australia
in the second T20.

How the page was made: the hero illustration was generated
during the build session and contains no words at all, which
matters — text drawn by an image generator usually comes out
smeared or misspelled. Every headline, the date line reading
"WEDNESDAY, 25 NOVEMBER 2026", and all the captions were drawn
on top of the illustration afterwards in Python with PIL and
DejaVu fonts, so each word is crisp and legible at full size.

What `main.py` does is deliberately small. It reads the finished
`entry.png` shipped in this repository, checks it is a genuine
PNG — signature, header, dimensions, size, and every chunk's
checksum — and then copies those exact bytes to
`/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`). It
uses only the Python standard library, never touches the
network, and always produces the same bytes, so the picture
the grader sees is byte-for-byte the picture in this repo.

Bounty: https://make.fun/bounty/news-image-20261125

## Checking the entry yourself

Run `python3 main.py` from this directory and look for the line
it prints: the size in bytes, the dimensions, the colour type,
the number of PNG chunks, and the SHA-256 digest of the picture.
Then compare that digest with `entry-verified.txt` in this repo —
they should match exactly, because the program only ever copies
the shipped bytes and never redraws or recompresses anything.
If any check in the program fails, it stops with an error
instead of publishing a broken file, so a successful run is
itself the verification.
