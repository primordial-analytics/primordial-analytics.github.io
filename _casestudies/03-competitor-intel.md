---
title: Competitor Intelligence
subtitle: Counteract and expand
layout: default
modal-id: 3
date: 2018-07-01
thumbnail: competitor-thumbnail.png
---

[alt]: 'sunshine-over-the-struggle'
[image]: img/case_studies/competitor.png

**Client's Problem:** _"We operate in a hypercompetitive industry where our
products have slim margins and the differentiation within a market is
service-level and not product-level. The issue we have is not knowing
how competitor behaviors and strategies impact our sales. We struggle
with the basics like pricing to capture the value proposition of our
service over competitors. Even simpler things, like when and where and
how to execute product decisions, are poorly understood outside of the
tribal knowledge of our product managers, making long-term strategic
decisions extremely difficult. All of this work is also very labor
intensive and the drudgery of it all distracts our talented people
from doing other more valuable work."_

![alt][image]{: .img-fluid }

We have a couple former product managers on our leadership team, and
this is a very common problem for retailers of any scale. Most
companies avoid the problem of competitor intelligence all together by
washing it out (sometimes rightly) using one of the standard product
management policies, e.g. margin, premium, etc. During scoping, we
determined there was sufficient evidence and data to pursue a more
sophisticated approach which was ultimately adopted.

The Client was a large national company, and they did indeed have a
very large number of competitors. Using the Client's existing industry
data, our first step was to determine if there were patterns in the
sales, demand, and competitor data. We found strong signatures of
competitor behavior impacting sales that was well-described by game
theory. With this discovery, we automated codification of the
rules and actions seen in the games to build a data set which could be
modeled. Using this game characterization data, we created several
machine learning-based models that were ensembled to predict when,
where, and how a competitor would make moves to capture demand.

Interestingly, these models performed poorly during the
experimentation phase. What we learned in the experiments was that
there was also a strong spatial component to the competitor behavior
not evident in the original data. Competitors also had complex, but
quantifiable, interactions over time, indicating structured network
effects. We modeled both of these patterns in-tandem using a novel
approach based on neural networks. The entire modeling backend was
automated into an intelligent agent that our Client's analysts
interacted with. The speed and efficiency of this new capability
enabled rapid testing of sophisticated strategic scenarios they had
never contemplated previously.
