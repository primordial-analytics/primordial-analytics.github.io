---
layout: post
title: Custom Website in 30 Minutes
description: Setup and Build a Web Site on a Custom Domain
comments: true
tweets: true
---

This time I truly mean it: hello, world! I have owned the
domain kcavagnolo.com for many years, and I never did anything
with it. The plan had always been to expos&eacute; some aspect of
my work, which at the time was astrophysics research. But, those
efforts usually fell into job hunting season and polishing a site
to accompany my resum&eacute;'s.

Well, now that I have been out of academia for several years,
and I have dabbled long enough in "data science" activities to
have a decent portfolio of stuff to share -- this site finally
made sense. After 24 hours of mucking around, it's finally
working correctly and I can post to it as a remote platform via
some cool automated tools I coded up. Without further ado, the
details of how the site came to be, and the accompanying code so
someone else can do the same thing.

First things first: bite the bullet and buy a custom
domain. The simplest route I've found in years is <a
href="http://domains.google.com" target="_blank">Google
Domains</a>. Prices are competitive and the interface is
intuitive. I recommend choosing to keep the registrar info
private during registration, it cuts down on spam and won't
expose personal info to an unknown audience.

After you've got a custom domain secured, and if you're not
hosting a commercial site, use <a href="https://pages.github.com"
target="_blank">GitHub Pages</a> as the hosting service. It's
free, robust, and super simple if you're comfortable with coding
in HTML5 and Git. The catch is that all website code will be
public unless you have a paid GitHub account and create a private
repository. Once you follow the tutorial in the link above, <a
href="https://help.github.com/articles/adding-a-cname-file-to-your-repository/"
target="_blank">setup CNAME file</a> which points back to your
newly acquired custom domain. This step connects your custom
domain to your GitHub domain <strong><em>on the GitHub side
only</em></strong>.

To connect the domains on the Google side, go back to Google
Domains, and on the dashboard, click the DNS icon for your
purchased domain name. At the top, select the radio button next
to the Google name servers. At the bottom, setup the panel like in
the image below. These settings instruct Google to allow the
connection of the domain names. If you wait 10-15 minutes, the
records will update in the tubes of the internet, and you should
be able to type in your domain name in a browser and not get a
404 error.

<img class="img-basic"
src="http://www.kcavagnolo.com/img/gdomains.png" alt="DNS Setup">

Cool, you've got a live connection behind-the-scenes if you
don't get a 404. So, what now? Let's put up a web page. I am a
big fan of the folks at <a href="http://startbootstrap.com"
target="_blank">Start Bootstrap</a> because I believe in what
they're doing for web design and their content is open
source. Look through the templates, pick one you like, and click
'Download.' Unpack the zip file into your GitHub Pages
repository. For now, that's all you need to do. If you visit your
domain name again, instead of seeing a blank page or some default
message from Google, you should see the template you
downloaded. It's not just a domain anymore, it's a web
site. Congrats, get to modifying the template HTML!

If you'd like to go one step further and add an email address
for your custom domain, e.g. ken@kcavagnolo.com, this can also be
accomplished without much effort. I highly recommend using GMail
for forwarding services for a variety of reasons. There is a
walkthrough about <a
href="https://support.google.com/domains/answer/3251241?hl=en"
target="_blank">adding email forwarding in Google Domains</a>. Be
sure to read the section at the bottom about sending email from a
forwarding address.

One more step I need to describe is building a local instance
of github pages and projects w/ jekyll, and installing
jekyll-bootstrap to handle plumbing/subdir instance of a blog
(like this one). The shit that's still broken:

* fancybox
* ipython integration
* plotly integration
* native code highlighting, like the below

{% highlight python linenos %}
def build_model(X, X_test, y):
model = DecisionTreeClassifier()
samples = sc.parallelize(Bootstrap(y.size))
vote_tally = samples.map(lambda (index, _):
model.fit(X[index], y[index]).predict(X_test)
).map(vote_increment).fold(zero_matrix(n_test, n_ys), np.add)
y_estimate_vote = np.argmax(vote_tally, axis = 1)
return accuracy_score(y_estimate_vote)
{% endhighlight %}
