# P0-G/H/I HBUT institutional-review email draft acceptance

**Decision:** `PASS_DETERMINISTIC_HBUT_EMAIL_DRAFT_PREPARED_WITHOUT_SENDER_NOT_SENT`

**CAS Q3 STATUS: NOT READY.**

The validated HBUT review-request ZIP is now attached to a deterministic RFC
5322/MIME email draft addressed to the official general contact
`kyc@mail.hbut.edu.cn`. The body asks for the applicable CAS upgraded-edition
year, Applied Intelligence title/ISSN and Computer Science major-category tier,
pre-submission manuscript approval, project-code release review and third-party
model boundary. It explicitly states that the draft and attachment supply no
institutional decision or authorization.

Two independent builds are byte-identical:

- `E:/paper/ReliableRAG-hbut-institutional-review-email-draft-20260915-c/hbut_institutional_review_request_draft.eml`
- `E:/paper/ReliableRAG-hbut-institutional-review-email-draft-20260915-d/hbut_institutional_review_request_draft.eml`

The `.eml` SHA-256 is
`34ac643f5059436274e6368d3bf3ced758298d79ce5ec6c653173a80acad5b75`
and its size is 562,539 bytes. Its sole attachment is the previously accepted
11-member packet with SHA-256
`42f533f6fba88b3d7367477ed27173ea49692f2eaf3e3abff8e85dbe76f13c5b`.
Each draft passes 43 header, body, MIME and attachment checks without extracting
the ZIP. All six targeted tests pass.

The draft deliberately has no `From`, `Sender`, `Date`, `Message-ID`, `Cc`,
`Bcc`, `Reply-To` or `Received` header. Its body contains a visible instruction
for the responsible sender to add their identity and contact details and to
review the recipient and attachment before sending. No SMTP client, browser or
mail account was opened or invoked.

## Preserved failure and correction

The first targeted run produced two failures because the original 64-character
custom attachment-hash header exceeded the recommended email line length. The
standard serializer folded it and the parsed unstructured value acquired
semantic whitespace, so exact header validation correctly rejected the draft.
The final format carries the same hash in two fixed 32-character headers and
recombines it only for validation.

The first provenance-label correction then produced the same two failures when
the descriptive packet-acceptance header itself exceeded the line limit. The
final length-safe header is `X-ReliableRAG-Packet-Commit`; the body defines it as
the review packet's accepted repository revision. The earlier a/b drafts are
retained as unsent superseded candidates. The request-packet bytes were unchanged.

Local validation passes 157 CAS Q3 tests and the complete repository suite
passes 431 tests with two documented Windows platform skips. The reviewer map
authenticates 213 repository records, and the fail-closed top gate authenticates
245 repository hashes while retaining `NOT_READY`.

## External boundary

The `.eml` has not been sent or imported into a mail client. No institutional
response exists. This acceptance does not verify the CAS tier, approve the
manuscript, establish the copyright holder, approve code release, authorize
distribution or submission, or close P0-G, P0-H or P0-I. Any later manuscript
approval remains subject to exact final author-artifact and SHA-256 rebinding.
