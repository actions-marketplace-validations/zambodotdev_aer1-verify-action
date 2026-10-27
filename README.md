# verify zambo receipts

checks every zambo receipt link in a pull request, and every receipt file you point it at, and fails the build if any does not verify.
a receipt proves the saved bytes are unchanged since the call ran. it does not judge whether the answer was right.

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

inputs:

- `paths`: files or glob patterns to scan for receipt links, comma or newline separated. receipt files saved as json with an `id` field are picked up too.
- `require-receipts`: set to "true" to fail the build when no receipts are found at all.
- `include-comments`: also scan pull request comments. defaults to "true".

want receipts on your own ai work so this check has something to verify? https://zambo.dev/add/?ref=verify-action

---
next step: add zambo to your ai in one url, no key, no account: https://zambo.dev/add/?ref=verify-action
got a receipt link from someone? check it in seconds: https://zambo.dev/verify/
every call returns a receipt. a receipt proves the saved bytes are unchanged. it does not prove the answer is right.
