# Primordial Analytics Consulting, LLC

Welcome to the open source repo for [our web site](https://www.primordialanalytics.com)! We strongly believe in the value of open source and sharing knowledge that has common value. Feel free to dig around in our code and see how we've modified a free template from Start Bootstrap.

## Howto's

### Semantic Versioning

To update the version of the site that has been released, use [`bumpversion`](https://github.com/peritus/bumpversion):

```bash
bumpversion minor --verbose
git push origin --tags
```

### HTML5 Movie

One of our founders has an affinity for cosmology and astrophysics: it's in the name, the logo, the font face, and our theme. So that movie on the front page, how did we make that? It's super simple:

```bash
# get a movie file to work
wget https://nasaviz.gsfc.nasa.gov/vis/a010000/a010600/a010661/Galaxy_Evolution-tracking_shot2-1080p.mov

# transform to an HTML5 friendly mp4 format
ffmpeg -i Galaxy_Evolution-tracking_shot-1080p.mov -vcodec copy -acodec copy galaxy.mp4

# compress the movie so it runs faster
ffmpeg -i galaxy.mp4 -filter:v "setpts=0.5*PTS" a.mp4

# trim to fit visually
ffmpeg -i a.mp4 -t 19 -c copy b.mp4
```

### Building the Site

Assuming Linux. Install Ruby and deps follwing the [instructions here](https://jekyllrb.com/docs/).

```bash
gem install bundler jekyll
```

To rebuild the site from scratch and capture config updates and styles changes, run the gulp command and then build the site:

```bash
gulp default
bundle exec jekyll serve --watch --trace --drafts --verbose
```

To run maintenance tasks, use `bundle` or `npm`:

```bash
bundle update
bundle install
bundle exec jekyll serve --watch --trace --drafts --verbose
npm audit
npm audit fix
```

## Attributions

With the exception of a few dollars per month in AWS charges and our personal time, our web site was built for free. Why wouldn't we pay someone? Our web site is partly to demonstrate the power of the analytical individual and the strength of the open source community. When consultancies launch into wanting to sell software XYZ from proprietary vendor ABC, it's a way of creating lock-in for long-term work -- this is a linchpin in the "land and expand" business model. At Primordial, we take the opposite view: we want you to see our work and for your people to have access to the code. That's what we've done with our site.

- [GitHub Pages Hosting](https://pages.github.com/)
- [Jekyll Blog Framework](https://jekyllrb.com/)
- [Startup Bootstrap Site Template](https://startbootstrap.com/template-overviews/agency)
- [Startup Bootstrap HTML5 Snippets](https://startbootstrap.com/snippets/)
- [NASA Galaxy Image](https://images.nasa.gov/details-PIA12348.html)
- [NASA Galaxy Video](https://nasaviz.gsfc.nasa.gov/10661)
- [Coverr MP4 Videos](https://coverr.co)
- [Unsplash Stock Photos](https://unsplash.com)
- [Fontawesome Icons](https://fontawesome.com)
- [Noun Project Logos](https://thenounproject.com/S-Copinger/uploads/?i=11524)
- [Font Squirrel Fonts](https://www.fontsquirrel.com/fonts/sansation)
- Communications powered by [AWS](https://aws.amazon.com/):
  - API Gateway (email form)
  - CloudWatch (API logs)
  - Lambda (form processing and email sending)
  - SES (send email)

## Copyright and License

Copyright &copy; 2019 Primordial Analytics Consulting, LLC.

Web site project code is released under the [MIT License](LICENSE.md).

Blog content is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](http://creativecommons.org/licenses/by-nc-sa/4.0/).

## Disclaimer

Primordial Analytics Consulting, LLC., hereafter, "The Owner."

Any views or opinions represented on this site or blog are personal
and belong solely to The Owner and do not represent those of people,
institutions or organizations that the owner may or may not be
associated with in professional or personal capacity, unless
explicitly stated.

Any views or opinions are not intended to malign any religion, ethnic
group, club, organization, company, or individual.

The Owner will not be liable for any errors or omissions in this
information nor for the availability of this information. The Owner
will not be liable for any losses, injuries, or damages from the
display or use of this information.

### No warranties

All content provided on this site or blog is for informational
purposes only. The Owner of this site or blog makes no representations as to
the accuracy or completeness of any information on this site or found
by following any link on this site.

This website is provided “as-is” without any representations or
warranties, express or implied. The Owner makes no representations or
warranties in relation to this website or the information and
materials provided on this website.

Without prejudice to the generality of the foregoing paragraph, The
Owner does not warrant that:

- this website will be constantly available, or available at all; or
- the information on this website is complete, true, accurate or non-misleading.

Nothing on this website constitutes, or is meant to constitute, advice
of any kind. If you require advice in relation to any technical,
legal, financial or medical matter you should consult an appropriate,
licensed professional.

### Limitations of liability

The Owner will not be liable to you in relation to the contents of, or
use of, or otherwise in connection with, this website:

- to the extent that the website is provided free-of-charge, for any direct loss;
- for any indirect, special or consequential loss; or
- for any business losses, loss of revenue, income, profits or anticipated savings, loss of contracts or business relationships, loss of reputation or goodwill, or loss or corruption of information or data.

These limitations of liability apply even if The Owner has been
expressly advised of the potential loss.

### Exceptions

None.

### Reasonableness

By using this website, you agree that the exclusions and limitations
of liability set out in this website disclaimer are reasonable.

If you do not think they are reasonable, you must not use this
website.

### Unenforceable provisions

If any provision of this website disclaimer is, or is found to be,
unenforceable under applicable law, that will not affect the
enforceability of the other provisions of this website disclaimer.

### Downloadable Files and Images

Any downloadable file, including but not limited to pdfs, docs, jpegs,
pngs, is provided at the user’s own risk. The Owner will not be liable
for any losses, injuries, or damages resulting from a corrupted or
damaged file.

### Comments

Comments are welcome. However, the site or blog owner reserves the
right to edit or delete any comments submitted to this site or blog
without notice due to :

- Comments deemed to be spam or questionable spam.
- Comments including profanity.
- Comments containing language or concepts that could be deemed offensive.
- Comments containing hate speech, credible threats, or direct attacks on an individual or group.

The blog owner is not responsible for the content in comments.

This site or blog disclaimer is subject to change at anytime.
