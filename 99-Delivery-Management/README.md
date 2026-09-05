# Delivery Management Playbook

A working reference for running software delivery: people, process, finance, and metrics — written from 15+ years leading delivery teams from 10 to 40+ people, across commercial software services and enterprise IT.

This is not a generic management guide. It's a structured record of what actually worked, including the parts that are unglamorous — revenue recognition mechanics, ticket-status SLAs, and why "plans are worthless, planning is invaluable" isn't just a slogan.

## Who this is for

Anyone stepping into (or hiring for) a Delivery Manager / Engineering Manager / Head of Delivery role, and anyone who wants to see how the job actually breaks down day to day rather than a title on a slide.

## Contents

- [Core Principles](#core-principles)
- [Role of a Delivery Manager](#role-of-a-delivery-manager)
- [People Management](#people-management)
- [Operational Management](#operational-management)
- [Requirements & Governance Design](#requirements--governance-design)
- [Finance Management](#finance-management)
- [Monitoring & Metrics](#monitoring--metrics)
- [First 90 Days in a New Delivery Role](#first-90-days-in-a-new-delivery-role)
- [Key Challenges and Lessons Learned](#key-challenges-and-lessons-learned)
- [Notes on Management](#notes-on-management)

---

## Core Principles

- **Empathy is essential — feel the room, not just read it.** Effective management isn't just about process; it's understanding what people actually feel, not just what they say. This is what resolves conflicts and keeps a team motivated.
- **Feedback is not a personal choice, it's a business decision.** Structured, data-driven, tied to goals and outcomes — that's what keeps it fair and removes personal bias.
- **Praise publicly, criticize privately.** Public recognition reinforces good behavior; private correction preserves dignity.
- **Plans are worthless, planning is invaluable.** The plan will become obsolete. The discipline of planning — giving everyone a shared understanding of direction and what to expect — is what survives contact with reality.
- **Results matter.** At the end of the day, the bottom line is the bottom line.

## Role of a Delivery Manager

A Delivery Manager's responsibilities split into four areas:

1. **People Management** — hiring, onboarding, feedback, growth plans, salary negotiations, exits, team allocation.
2. **Operational Management** — planning, capacity management, bottlenecks, escalations, SLAs, efficiency.
3. **Financial Management** — revenue outlook, billing, cost/margin performance.
4. **Data & Reporting** — the monitoring and metrics layer that makes the other three visible and manageable, rather than felt.

Customer relationship ownership is deliberately not on this list — in most setups it belongs to an Account Manager. The DM's main accountability is the delivery team, though they still engage with customers when it matters.

## People Management

A delivery team of 30-40 has a rough shape: ~65% engineers, ~30% analysts, ~5% QA/account management — organized into smaller pods of 6-10, with the DM overseeing several pods at once. Some people run independently; others need real intervention. **Postponing a people issue almost always makes it worse**, not smaller.

### Hiring
Driven by backlog growth, attrition, or a capability gap — never speculative. HR defines requirements and screens; the delivery team runs technical/fit evaluation; higher management aligns on salary band and headcount. Be transparent with candidates about the role and its real challenges, and document what's agreed for later reference.
> Mistakes in hiring are extremely costly in time, morale, and money — the upfront diligence is cheap by comparison.

### Onboarding
Assign a mentor. Set explicit expectations for the first months, with check-ins every two weeks and a formal review at the end of each of the first three. Gather feedback from both the mentor (technical/cultural fit) and HR (process experience). If it's clearly not working, part ways early — a bad fit compounds.

### Feedback
Feedback is a structured, data-driven process about performance and growth — not a personal preference exercise, and not the same process as a salary review (though the two are correlated). Structure each conversation around three parts: analysis of past performance, peer/colleague input gathered in advance, and goals for the next period. Document outcomes and revisit them at the next cycle. Regular check-ins are for progress and blockers; they don't substitute for the formal review.

### Exits
**Voluntary:** run an exit interview, agree how the departure will be communicated to the team, and assess impact on ongoing work before the person leaves — not after. The goal is a managed transition with no surprises for the team, and the departing person leaving on good terms.

**Involuntary:** rare, and requires real preparation — documented performance or conduct issues, prior conversations on record, and alignment with HR/management before acting. Communicate the decision transparently and respectfully, and address the team promptly to prevent uncertainty from spreading.

### Team Allocations
Review backlog vs. capacity regularly. A rough rule of thumb: a healthy team's backlog should represent about 2-3 months of work — materially longer or shorter, and it's time to redistribute work or adjust FTE.

### Salary Negotiations
Adjustments are driven by performance, market rate, and budget — not by whoever asks. Weigh individual and team performance, internal parity, replacement cost, and company financial health together, and be transparent about the criteria even when the answer is "not now."

## Operational Management

Weekly planning, daily standups, and capacity reviews are the mechanism that keeps delivery predictable rather than reactive.

- **Transparency** — share goals and risks before they become surprises.
- **Collaboration** — align priorities across the team through regular, structured conversation, not ad hoc pings.
- **Proactivity** — adjust commitments before they slip, not after.
- **Efficiency** — keep meetings short and decision-focused; let data carry the routine status updates.

### Backlog Overview
The DM's central job: keep the backlog visible and honest — priorities, stuck items, commitments (legal, contractual, client), budget discrepancies, and quality signals (bug counts, SLA adherence) all live here.

### Weekly Planning
Agree the next 1-2 weeks of work, surface dependencies and stuck items, and re-estimate anything new. Everyone should leave knowing what they own and why.

### Daily Standups
Fifteen minutes, team-led, focused on "who's stuck" and immediate blockers — not a project deep-dive. The DM typically listens rather than runs it.

### Ad-hoc / Project-based Planning
Large or complex initiatives get their own cadence — define what counts as "big," pull in the right people (architects, account managers), and agree how the customer is involved.

### Capacity Planning
Split the backlog into what's committed ("hard") and what's contingent on client input or prioritization ("indicative"). Match that against available FTEs to build a realistic calendar outlook, and revisit it monthly with management, not just weekly with the team.

## Requirements & Governance Design

The mechanics of "how an idea becomes shipped work" — the part that prevents both a) verbal, undocumented requirements causing rework, and b) heavyweight process on things too small to need it.

### What / How / Build ownership split
A clean accountability model, regardless of who's in which seat:
- **Requirements owner** defines *what* needs to happen and *why* — business need, UI/data implications, acceptance criteria. Nothing gets handed off "empty"; if there's no acceptance criteria, it's not ready to move.
- **Solution/architecture owner** defines *how* — data model impact, integration points, risks and alternatives. Work isn't done until this is written down; "it's in my head" isn't a deliverable.
- **Implementation owner** builds against both, and flags back upstream the moment either the "what" or the "how" is unclear rather than guessing.

This split matters most exactly where teams skip it under time pressure — and that's exactly when skipping it gets expensive.

### Written-artifact threshold
Everything above a size/impact threshold (roughly: more than a couple hours of work, any new/changed UI, any data-structure or integration change) gets a short written description before work starts — what, why, and how it'll be judged done. Below that threshold, don't bother; the overhead isn't worth it.

### Architecture review gate
Make architecture review mandatory for a specific, narrow list of triggers rather than "use your judgement" — data model changes, cross-system integrations, new technology, or anything past a size threshold. A short, explicit checklist beats a vague expectation that people will "loop in architecture when it matters" — they won't, consistently, without one.

### Ticket-status SLA framework
Give every ticket a defined lifecycle (submitted → triaged → assigned → in analysis → in progress → queued → in testing → deferred → closed/done/rejected) and attach an SLA to each *transition*, not just the end-to-end time. The rule that does the most work: **no ticket sits in a status without a comment past a defined interval** — silence, not slowness, is what erodes trust in the process.

### Capacity rule
Plan roughly **60-70% of theoretical team capacity**; reserve the remaining **30-40% as buffer** for incidents, unplanned work, and new intake. This one number prevents more replanning thrash than any amount of individual task-level accuracy.

### Guiding triad
> **Predictability over reactive firefighting.**
> **Transparency over silence.**
> **Delivery over justifications.**

## Finance Management

### Revenue Recognition
Recognize revenue conservatively and proportionally to actual progress — not against speculative or unordered work. Example: a 100-hour task with 60 hours done and client-ordered work in progress recognizes revenue for the 60; if client acceptance is still pending, apply a risk discount and recognize less.

### Billing Outlook
Align billing milestones with the client during project planning, and produce a monthly billing report covering hours worked, milestones hit, and pending approvals — predictable cash flow starts with predictable invoicing.

### Finance Outlook
Forecast revenue, cost, and risk from known backlog, capacity, and client priorities. Watch specifically for outliers: underperforming projects, delayed client payments, misallocated resources — these are where financial surprises actually come from, not the averages.

### Monthly Review
A recurring review involving delivery, finance leadership, and account management — reconcile the prior month, agree the outlook for the next one, and keep everyone aligned on the same numbers.

### Principles
Conservatism, accuracy, transparency, proactivity — in that order of priority when they conflict.

## Monitoring & Metrics

The goal of monitoring is to **automate the routine so attention goes to the exceptions** — not to build a bigger dashboard for its own sake.

### What to automate
Estimates vs. actuals, blockers, SLA compliance, time-in-status, lead time, cycle time (split into time-on-us vs. time-on-customer), and bug trends (count, resolution time, priority mix).

### Time logging
Useful only if the *why* is communicated clearly: it exists to understand where time actually goes and make better decisions, not to micromanage. Teams that treat it as a punishment measure get bad data; teams that treat it as a shared instrument get good data.

### Management by exception
Don't review what's on track. Review estimate deviations, off-track projects, unresolved blockers, and SLA breaches — and hold periodic retrospectives to catch systemic issues before they recur.

### Core KPIs
1. **Profit margin** — revenue vs. cost, by project and by team.
2. **Capacity utilization** — delivered vs. time spent; over- or under-utilization.
3. **Quality** — bug count, resolution time, effort spent on defects.
4. **Overspend indicator** — actuals vs. estimate, flagged at both individual and team level.
5. **Lead time** — task initiation to completion.
6. **Cycle time** — broken into internal-processing vs. customer-waiting phases.
7. **Productive time** — billable work as a % of logged hours.
8. **Client/task-size analysis** — correlating task size with overspend, bug rate, and complexity.

### Reports & Dashboards
Two audiences need different views: the delivery team needs backlog outlook, issue/bug status, and time-allocation detail; delivery *management* needs profit margin, revenue, billing health, and project-level financials rolled up. Build both — a single dashboard trying to serve both audiences usually serves neither well.

## First 90 Days in a New Delivery Role

A repeatable ramp-up sequence for stepping into a new delivery/DM role, rather than improvising it each time:

1. **Get the lay of the land** — existing project plans if any exist, current team roles, and where things actually stand vs. where documentation says they stand.
2. **Run working sessions with the core team** — don't rely on org charts; interview people directly to find the real stakeholders and the real pain points.
3. **Establish the lead relationship** — build working sessions and trust with the business lead(s) early; this relationship is what everything else depends on.
4. **Align expectations and goals explicitly** — don't assume shared understanding of success; write it down and confirm it.
5. **Position yourself as the bridge**, not a bottleneck, between business and delivery.
6. **Name the risks out loud early** — lack of structure and lack of alignment are the two most common failure modes in a new role, and both compound if unaddressed in the first weeks.
7. **Agree a communication plan and a phased rollout** for any process changes, with feedback loops built in rather than a single big-bang change.

## Key Challenges and Lessons Learned

- **People are everything.** A motivated, supported team delivers; everything else is downstream of that.
- **Take care of your team first.** Structured feedback and fair reviews beat good intentions; don't avoid the hard conversations.
- **Data beats assumption.** Decisions made on evidence outperform decisions made on confidence — build the monitoring before you need it, not after something goes wrong.
- **Transparency is a constant balancing act.** Sharing performance and time data builds trust only if the *why* is communicated honestly — the same data shared without context reads as surveillance.

## Notes on Management

Raw, ongoing notes — the parts too short to be a section on their own but too useful to leave out.

**Leadership & team dynamics**
Be careful with divas; tolerate with caution. Unethical behavior is a hard no. Praise publicly, criticize privately. People are everything. Involve everyone. Feel the room, don't just read it. Everything is a trade-off — know which ones you're making.

**Productivity & execution**
Results matter. Better done than perfect. Don't avoid hard conversations. Everyone — including the manager — should be able to say what they did today and this week. Maintain predictability and accountability. Data beats guessing. Sometimes good enough is enough.

**Values & decision-making**
When things get tense, come back to goals and values. No compromises on values. Don't tolerate low quality. Plans are worthless, planning is invaluable.

**Growth & feedback**
Feedback is a business decision, not a personal one. Learn from mistakes — yours included. Take care of your team. Reward intrinsic motivation.

**Communication & accountability**
State the vision and the expected action clearly. Everyone can be someone else's accountability partner. Listen before speaking. Be crystal clear about expectations.

**Adaptability & change**
Change is inevitable — accept it and drive it, don't just survive it. Favor self-organization over top-down control where the team has earned it.

---

*This is a living document — sections will expand as more of the underlying material gets written up.*
