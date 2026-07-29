# Security policy

## Reporting a vulnerability

Do not open a public issue for a vulnerability involving credentials, private
data, dependency compromise, or unintended network access.

Report it through GitHub's private vulnerability reporting for this repository.
If that option is unavailable, email `mazzapaolo2019@gmail.com` with the subject
`google-news-api security report`.

Include:

- The affected `google-news-api` version.
- The impact and conditions required to reproduce it.
- A minimal reproduction with all credentials and private data removed.
- Any suggested mitigation.

Do not include `SEARCHAPI_API_KEY`, environment files, cookies, full request
headers, or private exported datasets.

The maintainer will assess complete reports and coordinate a compatible fix and
disclosure. No response-time guarantee is made for this volunteer-maintained
project.

## Supported versions

Security fixes target the latest published version. Older releases may require
an upgrade.

## Scope

This package uses undocumented Google News RSS and URL-decoding behavior.
Upstream response changes and temporary rate limits are compatibility defects,
not security vulnerabilities, unless they expose private data, credentials, or
create unintended network access.
