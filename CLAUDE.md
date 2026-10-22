# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Marketing site and blog for Primordial Analytics (<www.primordialanalytics.com>): a Jekyll site on the `github-pages` gem, built from the Start Bootstrap "Agency" template (Bootstrap 5, jQuery). There are no tests or linters. To verify a change, build the site and look at it.

## Commands

```bash
# Ruby: CI uses 3.1.4. System ruby is 3.0.2, so use the asdf install:
export ASDF_RUBY_VERSION=3.1.4
gem install bundler -v 2.5.23   # matches "BUNDLED WITH" in Gemfile.lock
bundle install                  # gems go to vendor/bundle (set in .bundle/config)
npm install

# CI-equivalent build check
JEKYLL_ENV=production bundle exec jekyll build

# Full rebuild: compile+minify SCSS and JS, copy vendor libs into libs/, then jekyll build
npm run build         # = npx gulp default

# Local dev server with live reload (Jekyll only; does NOT recompile SCSS/JS)
bundle exec jekyll serve --watch --trace --drafts --verbose

# Dev with gulp watchers + BrowserSync serving _site/ (recompiles SCSS/JS on change)
npm start             # = npx gulp dev

# Individual gulp tasks (use npx: /usr/bin/gulp is a broken Debian package)
npx gulp css          # scss/ -> _includes/css/agency.css + agency.min.css
npx gulp js           # js/*.js -> js/*.min.js
npx gulp vendor       # node_modules -> libs/{bootstrap,jquery,jquery-easing}

# Release
bumpversion minor --verbose && git push origin --tags
```

## Build pipeline: generated files are committed

CI (`.github/workflows/jekyll.yml`) only runs `bundle exec jekyll build` on pushes to `master` and deploys to GitHub Pages. It never runs gulp or npm. So the outputs of gulp must be committed:

- **CSS**: `scss/agency.scss` (partials loaded via `@use`, and the order matters) compiles to `_includes/css/agency.css` and `agency.min.css`. Those files sit in `_includes/` because the root `style.css` is a Jekyll page whose layout (`_layouts/style.css`) runs `{% include css/agency.min.css %}`. After editing any `.scss`, run `npx gulp css` and commit both `_includes/css/` files. Otherwise the live site won't change.
- **JS**: pages load only the `.min.js` files (see `_includes/js.html`). After editing `js/*.js`, run `npx gulp js` and commit the `.min.js`.
- **Vendor libs**: `libs/` is copied from `node_modules` by `gulp vendor` and committed. (`vendor/` is something else: it's gitignored and holds the bundler gems.)
- Fancybox loads from cdnjs, only on `post` pages, and is deliberately pinned to 3.3.5 because newer versions broke the lightbox. The form-validation and `contact_me` scripts load only on the `home` layout (the contact form lives there). There is no icon font: icons are inline SVGs.
- The hero video (`img/galaxy.webm` / `.mp4`) has `data-src` sources that `js/agency.js` fills in only on wide, hover-capable screens without reduced motion. Elsewhere the header shows `img/galaxy-poster.webp`.

## Content model

Each page is assembled by a layout in `_layouts/` from partials in `_includes/`:

- `home` (used by `index.html`): header, services, about, latest_posts, testimonials, contact. The about section loops over `site.team`.
- `default`: a `small_header` (which shows `page.title` / `page.description`) plus the page content. `people.html`, `process.html`, `projects.html`, `community-health-data-help.html` (the main landing page for organizations seeking free help) and the case-study pages use it. `projects.html` renders `portfolio_grid.html`, whose cards link to each `/casestudies/<slug>/` page.
- `blog` / `post`: `blog_body.html` lists `site.posts`. `post_body.html` renders a post and includes Disqus.

The collections are defined in `_config.yml`. Their front matter feeds the includes, and images resolve by convention:

| Collection       | Key front matter                                     | Image path                       |
| ---------------- | ---------------------------------------------------- | -------------------------------- |
| `_team/`         | `name`, `position`, `pic`, `blurb`                   | `img/team/{{pic}}`               |
| `_testimonials/` | `quote`, `name`, `title`, `pic`                      | `img/testimonials/{{pic}}`       |
| `_casestudies/`  | `title`, `subtitle`, `date`, `thumbnail`             | `img/case_studies/{{thumbnail}}` |
| `_posts/`        | `layout: post`, `title`, `description`, `comments`   | anywhere under `img/`            |

Posts get the permalink `/blog/:title/`. Post images use a custom `<blog-figure>` element, styled in `scss/_figures.scss` / `_blog.scss`.

Only `casestudies` and `posts` output their own pages. `team` and `testimonials` set `output: false` and render only through the home page includes. Every layout puts a skip link first and wraps page content in `<main id="main">`. The blog index lives at `/blog/` (with `redirect_from: /blog.html`).

## External integrations

- Contact form: `js/contact_me.js` POSTs JSON to an AWS API Gateway endpoint (backed by Lambda + SES). The backend isn't in this repo.
- Google Analytics (gtag) and the Bing/Google verification files (`BingSiteAuth.xml`, `google*.html`, the `msvalidate` meta tag) are live. Don't remove them.
- SEO/sitemap/feed/redirects come from the `jekyll-seo-tag`, `jekyll-sitemap`, `jekyll-feed`, and `jekyll-redirect-from` plugins. Every page defaults to the share image `img/sm_content/og-default.jpg` (front-matter defaults in `_config.yml`). The Google verification file is kept out of the sitemap with `sitemap: false` but must stay published.
- The contact form's JSON payload must keep exactly the keys `name`, `phone`, `email` and `message`, because the backend schema is unknown. The "I am…" role is prepended to `message`. Never submit the form or POST to the endpoint in testing: it sends real email.
