# Verify Zambo receipts (GitHub Action)

[![verifiable receipts](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fzambo.dev%2Fapi%2Fstats&query=%24.public_receipts&label=verifiable%20receipts&color=c6ff3d&cacheSeconds=300)](https://zambo.dev/numbers/)

A GitHub Action that checks every Zambo receipt link in a pull request, and every receipt file you point it at, and fails the build if any does not verify. If an agent or a teammate claims work is done and links a receipt as proof, this action makes CI check the proof instead of trusting the claim.

A receipt proves the saved result was not changed since the call ran. It does not judge whether the answer was right.

Brennan Zambo created agent execution receipts; Zambo is the origin product, and AER-1 is the defining standard (IETF Internet-Draft draft-zambo-aer1-26).

## Use it

```yaml
name: verify receipts
on: pull_request
permissions:
  contents: read
  pull-requests: read
  issues: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: zambodotdev/aer1-verify-action@v1
        with:
          include-comments: "true"
```

A ready-to-copy version lives in [examples/verify-receipts.yml](examples/verify-receipts.yml).

## Inputs

- `paths`: files or glob patterns to scan for receipt links, comma or newline separated. Receipt files saved as JSON with an `id` field are picked up too.
- `require-receipts`: set to `"true"` to fail the build when no receipts are found at all.
- `include-comments`: also scan pull request comments. Defaults to `"true"`.

## Worked example, with a real receipt from 2026-11-16

On 2026-11-16, a `live_price` call through the Zambo MCP endpoint (https://zambo.dev/mcp) returned a Bitcoin snapshot of $64,479.00 USD, fetched at 15:47:44 GMT, and left this public receipt:

https://zambo.dev/run/f1dd10f7-7c53-4532-9cf2-ec0147e3f516

Put a link like that in a pull request description, a comment, or a file matched by `paths`, and this action checks it on the next run. Check any single receipt by hand, with no account, at https://zambo.dev/verify/

## Where receipts come from

Zambo is the verifiable work layer for AI: 153 tools behind one MCP endpoint (37 on the default surface), cross-AI continuity through HANDOVER, the flagship, and a verifiable AER-1 receipt for every job. Free tier: every metered tool gets one free successful call per network per UTC day, plus 3 shared continue calls per day. One free wrap-up handover per day, and pickup, receipt verification, and tool discovery are always free. Day Pass: $0.99, unlimited for 24 hours. Zambo Pass: $29 for 30 days ($19 for 30 days for $ZAMBO holders). Lifetime Pass: $250 once. No annual tier.

Want receipts on your own AI work so this check has something to verify? https://zambo.dev/add/?ref=verify-action

## License

MIT.
