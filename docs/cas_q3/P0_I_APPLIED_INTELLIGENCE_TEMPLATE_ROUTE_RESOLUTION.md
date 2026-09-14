# P0-I Applied Intelligence template-route resolution

**Decision:**
`PASS_OFFICIAL_PUBLISHER_ACCEPTS_CURRENT_SN_JNL_SUBMISSION_ROUTE_SMALLCONDENSED_STYLE_EQUIVALENCE_UNPROVED`

**CAS Q3 STATUS: NOT READY.**

The current Applied Intelligence submission page contains two instructions that
must be separated. Its main LaTeX guidance encourages the current Springer
Nature LaTeX template and asks for editable sources plus the compiled PDF. A
later legacy paragraph still names the `smallcondensed` option, but its linked
archive returns HTTP 404. Springer Nature's current official LaTeX support says
the current authoring template may be used for any Springer Nature journal,
subject to journal-level content and style instructions.

This establishes publisher acceptance of the current `sn-jnl` template as a
submission route for Applied Intelligence. It does not establish that `sn-jnl`
is visually or semantically equivalent to the unavailable legacy
`smallcondensed` profile. That style discrepancy remains disclosed rather than
being converted into a false equivalence claim.

The accepted engineering route is already concrete: the authenticated
December 2024 Version 3.1 package is pinned by hash, the source archive is flat,
two independent private transports are byte-identical, each passed 56 checks,
and both clean-compile to the exact 12-page PDF that passed project-lead visual
review. The route therefore no longer requires a separate pre-submission email
from the journal merely to establish that `sn-jnl` may be uploaded.

This closes only the pre-submission template-route gate. A real
author-populated package has not been built or uploaded, no Editorial Manager
compile has been observed, and no submission is authorized. Author facts,
institutional CAS evidence, release review and the final GPT-6 Astra xhigh audit
remain open.

Official sources inspected on 2026-09-14:

- <https://link.springer.com/journal/10489/submission-guidelines>
- <https://www.springernature.com/gp/authors/campaigns/latex-author-support>
- <https://support.springernature.com/en/support/solutions/articles/6000081241-templates-and-style-files-for-journal-article-preparation>
