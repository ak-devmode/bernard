# The Vector: Where Padma Is Going and Why It Matters

**Version:** 0.2 — Working Draft  
**Author:** Alex  
**Date:** March 2026  
**Status:** Draft — for internal team discussion

---

## 1. The Premise

Technology is about to reshape healthcare in ways that most people in this industry haven't internalized yet. Not in a vague "digital transformation" way — in a concrete, measurable, happening-right-now way. AI, automation, and data are collapsing the cost of things that used to be expensive: patient engagement, diagnostic review, care coordination, personalized communication. My 'hot take' is that this paradigm shift is not going to collapse jobs, but expand access to things like diagnostics to more (less wealthy) people. The organizations that understand this early and build for it will define the next era of healthcare delivery. The ones that don't will be selling the same service at the same price while the floor drops out from under them.

Padma is positioned to be one of the ones that gets it right.

We have three things that almost nobody else in Indonesia has simultaneously: 17 years of hands-on clinical operations, a growing model for high-touch patient engagement, and an in-house technology team building custom solutions for our exact needs. That combination is rare. It's also exactly what's required to take advantage of what's coming.

This document is a starting point — not a strategic plan. It's meant to frame how we think about the future, give us a shared vocabulary, and set a direction. The specific destination matters less right now than making sure we're pointed the right way and moving at the right speed.

## 2. The Parallelogram

Here's a mental model for thinking about our opportunity.

Draw two timelines side by side — "now" and "five years from now." On each timeline, mark two points: the global bleeding edge of healthcare technology (what's possible today in the best-funded, most advanced settings) and what's actually available and deployable in Indonesia.

There's a gap between those two points. There will always be a gap — regulatory environments, infrastructure, talent availability, and market readiness mean Indonesia trails the global edge. But the gap isn't fixed. It shifts. Sometimes it narrows. Sometimes it widens. And the entire frame moves forward over time.

Connect those four points and you get something like a parallelogram — a shape that represents the space of realistic opportunity for a company like ours. The global edge tells us what's *possible*. The Indonesia line tells us what's *practical*. And the five-year projection tells us where both lines are heading.

Right now, Padma sits somewhere in or near this shape. The question isn't "where exactly should we be in five years?" — it's "what vector (direction and velocity) should we be on so that as the shape shifts, we're inside it and moving with it?" 

This matters because organizations that pick an exact endpoint and aim for it tend to hit two problems: they either arrive at a destination that moved, or they course-correct so hard when they miss that the organization experiences whiplash. We want to set a vector — a direction and pace — so that future adjustments are tweaks, not resets.

## 3. What We're Already Building

These aren't hypotheticals. These are things that will be live this year.

**3.1 AI-Assisted Diagnostic Imaging (Kalpa PACS)**

We're building a PACS (medical imaging system) on open-source foundations with a machine learning layer that reviews X-ray images before a radiologist sees them. The neural network generates markup and a draft impression. The radiologist reviews, confirms or adjusts, and signs off. Target cost: under $1 USD per impression. This isn't replacing doctors — it's giving them a pre-screened, annotated starting point that makes them faster and more consistent. Nobody in Indonesia is doing this at this price point.

**3.2 AI-Enriched Patient Profiles**

Every interaction a patient has with us — chat, call, visit, inquiry — generates data. Right now, most of that data evaporates. We're building a system that ingests this dialogue continuously and constructs an evolving, AI-maintained profile of each patient: their health concerns, communication preferences, family context, engagement history. The profile gets richer over time and allows us to tailor every subsequent interaction. This is the foundation for genuine personalization at scale — not "Dear [First Name]" but actually understanding what someone needs before they tell us.

**3.3 Voice-to-Profile (Stream of Consciousness Medical History)**

Patients don't think about their health in structured forms. They think in stories — "well, my knee has been bothering me since I fell last year, and my mother had the same thing, and I've been taking something my neighbor recommended..." We're building a pipeline where patients can leave voice notes — stream of consciousness, no structure required — and our system converts speech to text, extracts medically relevant information, and feeds it into the same patient profile engine. Low friction for the patient. High value for us.

All three of these share a common thread: they use AI to do things that were either too expensive, too slow, or too labor-intensive to do before — and they all feed a central asset: a deep, continuously improving understanding of each patient.

## 4. Where the Bleeding Edge Is Going

This section is intentionally incomplete — it's one of the things we'll build out together in the Vector Meeting. But here's a frame for the kind of things happening globally that should inform our thinking:

**Diagnostics and imaging.** AI-assisted radiology is already outperforming human-only review in specific narrow tasks (mammography screening, diabetic retinopathy detection). Within five years, expect AI to be the *primary* reviewer for routine imaging, with humans in an oversight role — a complete inversion of today's workflow. Robotic diagnostic systems are advancing rapidly; the error rates for robotic-assisted procedures are trending toward fractions of their human-only equivalents.

**Patient engagement and care coordination.** The best global systems are moving toward ambient intelligence — AI that listens to doctor-patient conversations, generates notes, orders, and follow-ups automatically. The engagement layer is getting smarter: AI agents that can conduct intake interviews, triage symptoms, schedule appropriately, and follow up post-visit with personalized guidance. The cost of a meaningful patient interaction is collapsing.

**Data and risk modeling.** With enough longitudinal patient data, AI can predict health risks, flag early warning signs, and recommend interventions before symptoms present. This is moving from research to production in the US and UK. The implications for insurance and managed care are massive — if you can accurately model individual risk from behavioral and diagnostic data, you can price coverage far more precisely than traditional actuarial methods.

**Robotics.** Surgical robots are no longer experimental — they're becoming standard of care for an expanding list of procedures in the developed world. The market for robotic surgical devices is growing at over 13% annually. Current systems (Intuitive's da Vinci, Medtronic Hugo, and dozens of newer entrants) are surgeon-controlled, but the trajectory is clear: AI integration is steadily increasing the robot's role from instrument to collaborator. Meta-analyses of recent studies show robotic-assisted procedures achieving 30% fewer intraoperative complications and 40% improved precision compared to manual surgery. The autonomy scale runs from Level 0 (no autonomy) to Level 5 (fully autonomous) — most deployed systems today are Level 1-2, with a handful of Level 3 systems in clinical use for targeted applications like radiosurgery and corneal procedures. In a widely reported 2025 experiment at Johns Hopkins, an AI-trained surgical robot performed 17 sequential steps of a gallbladder removal with 100% accuracy in a simulated setting, responding to voice commands and self-correcting in real time. Full autonomy is still distant for complex surgery, but for routine diagnostic and minor procedures, semi-autonomous robotic systems will be clinically viable within five years. The implications for a market like Indonesia — where specialist surgeon availability is a genuine constraint outside major cities — are enormous. Robotics could eventually democratize access to procedures that currently require a patient to travel to Jakarta or Surabaya.

**Pharmaceuticals and path to market.** The drug development pipeline is being fundamentally reshaped by AI — not just in discovery (finding new molecules) but in the entire path from candidate to patient. AI-designed drug candidates are now showing 80-90% success rates in Phase I trials versus the historical average of roughly 52% for traditionally discovered compounds. Over 173 AI-originated programs are now in clinical development globally as of 2026, up from just 3 in 2016. More consequentially for the healthcare delivery side, regulators are adapting: the FDA phased out mandatory animal testing in 2025 in favor of AI-powered simulations and "new approach methodologies," and issued its first formal guidance on AI in drug regulatory submissions. Joint FDA-EMA guiding principles published in January 2026 are establishing common international standards. This matters for Indonesia not because we're developing drugs, but because the global acceleration of drug development and approval will increase the flow of new therapeutics into every market — and the organizations best positioned to evaluate, adopt, and deliver those therapeutics to patients will have a significant advantage. Indonesia's own regulatory apparatus (BPOM) will face pressure to modernize its approval pathways to keep pace with this global acceleration, and the organizations that understand the new landscape — that can read the evidence, interpret AI-generated clinical data, and integrate new therapeutics into care delivery quickly — will be the ones that capture value. The current regulatory environment in Indonesia is, frankly, years behind. But the gap will narrow because it has to — the alternative is that the country falls further behind on access to modern therapeutics, and the political and public health pressure to prevent that is real.

**The Indonesia lag.** Most of this is 3-7 years from broad availability in Indonesia. Regulatory frameworks (SATU SEHAT compliance, BPOM device approvals, OJK insurance licensing) move deliberately. Infrastructure gaps persist outside Java. Talent is concentrated in a few cities. But the gap is closing faster than most people think — SATU SEHAT's push for interoperability, the growth of the domestic tech talent pool, and increasing comfort with digital health tools among Indonesian consumers are all accelerating forces.

## 5. The Bigger Idea

This section is deliberately aspirational. It's not a plan — it's a direction to think in.

Healthcare and insurance have been separate industries for a long time. You get care from one set of companies and coverage from another. The boundary exists for historical and regulatory reasons, but it's increasingly artificial. If you control the care delivery relationship — if you *know* the patient, engage with them continuously, manage their health proactively — you have better data about their actual risk than any insurance company using traditional methods.

Technology is making it possible to imagine a world where these two things collapse into one relationship. A service that knows you, engages with you, helps you manage your health, handles the routine stuff affordably, and covers you if something catastrophic happens. Not insurance as it exists today — something new that only works because the cost of engagement has dropped (AI), the quality of risk data has improved (continuous profiling), and the care delivery is integrated (end-to-end operations).

Indonesia has roughly 48 million people in the middle class today and another 137 million in the aspiring middle class — people whose incomes are growing but who are poorly served by existing healthcare options. BPJS provides a baseline, but anyone who has used BPJS knows the constraints. At the same time, private insurance is expensive and feels disconnected from the actual care experience.

There is a large population — conservatively 45-65 million people, concentrated in urban areas — whose households earn enough to spend something beyond BPJS on their health, but for whom current private options are either too expensive or don't deliver obvious value. A service priced at Rp 150,000/month for concierge-level care coordination, with an optional Rp 500,000/month insurance layer backed by superior risk data, could serve this market in a way nothing currently does.

We don't need to build this tomorrow. We probably can't. But every capability we're developing — the AI profiles, the diagnostic automation, the engagement layer — is a building block toward it. And knowing that this is the direction we're pointed helps us make better decisions about what to build next.

## 6. Our Moat

Other companies are "using AI in healthcare." Halodoc has AI triage. Good Doctor has an engagement layer. Various insurtechs are selling policies online.

The difference is that everyone else is selling a service or a product. They're plugging AI into a specific function — triage, scheduling, claims processing. That's valuable, but it's modular and replaceable.

We own the full vertical. We operate clinics. We engage patients directly. We build our own technology. When we deploy AI, it's not a feature we're adding — it's woven into the entire experience from first contact to ongoing care. That means we can:

- Build patient profiles from *our own* first-party data across every touchpoint
- Train and improve models on *our own* clinical and operational data
- Customize the entire patient journey, not just one component of it
- Control quality end-to-end, not just at the points where a vendor's API is plugged in

This isn't a permanent advantage — others could build it. But they'd have to assemble the same combination of clinical operations, patient engagement, and custom technology. That's years of work, and we're already here.

## 7. The Vector, Not the Endpoint

We don't know exactly what healthcare looks like in Indonesia in five years. Neither does anyone else. But we can see the direction the technology is moving, we can feel the gap between global capability and local availability, and we know what we're good at.

The goal of the Vector Meeting — and this broader process — is not to pick a destination. It's to align on a direction and a pace. When new information arrives (a regulatory change, a technology breakthrough, a competitive move), we want to be able to adjust slightly rather than pivot dramatically. That only works if the underlying vector is sound.

The questions we need to answer together:

1. Where is the global bleeding edge of healthcare technology right now — not in research labs, but in actual deployment?
2. Where is the equivalent capability in Indonesia today?
3. Where will both of these be in five years?
4. Given that parallelogram: where should Padma be heading, and how fast?

Everything else follows from getting those four questions right — together, with the best information we can assemble.

---

*This is a living document. It will evolve as our thinking sharpens.*
