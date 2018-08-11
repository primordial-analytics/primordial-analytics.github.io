---
title: Customer Behavior
subtitle: Initial conditions are critical
layout: default
modal-id: 2
date: 2018-07-01
thumbnail: customers-thumbnail.png
---

[alt]: 'no-one-person'
[image]: img/case_studies/customers.png
[tree]: https://en.wikipedia.org/wiki/Behavior_tree_(artificial_intelligence,_robotics_and_control)

**Client's Problem:** _"Our sales transactions are pretty rich with
data, and we don't have any trouble reporting on that data or using
canned solutions from our CRM provider to determine customer lifetime
value (CLV) or predict churn.  Where we're struggling is in
determining how to engage with a customer next in order to maximize
our market share, not to maximize their spend necessarily, just their
number of purchases. A lot of the products we sell you can get
anywhere, and we want our service model to shine by getting people
regularly into our sales funnel."_

![alt][image]{: .img-fluid }

A very interesting problem, which concerned us, it didn't seem very
valuable to the Client at first glance to have an analytics team dig
on this problem. Market share is a difficult number to ascertain if
the Client is not in an industry with numerous public companies that
disclose data where one can reverse-engineer the market share per
company. That was the case here. However, what ultimately made a
solution tractable and valuable was that purchases were geospatially
related.

A common approach to customer behavior modeling is to consider the
purchase network or [behavior tree][tree]. Customers in the Client's industry
had a set of physical limitations that constrained their purchases,
adding to the behavioral tree a unique set of conditions that was
directly related to market share. As a result, we were able to build a
probabilistic model for how many purchases a customer should be making
in a period of time. Combined with the Client's existing churn and CLV
models, the behavior model was able to discern missing purchases from
non-existent purchases.

After segmenting and clustering the Client's customers, the clusters
were probed for actions which resulted in long-term growth in number
of transactions. We subsequently built an intelligent agent using
reinforcement learning to execute next best actions following a
purchase that had a high-probability of increasing future
transactions. The Client's sales team was able to use this agent to
reduce the amount of unnecessary "discounting" (e.g. coupons, bundles,
sales) to attract continued purchasing.
