# draw.io — static GitHub Pages mirror

Live editor: **https://coattails-droid.github.io/drawio-live/**

This repo hosts a **static mirror of the draw.io diagram editor**, built for free
hosting on GitHub Pages. No backend, no build step — just the deployable webapp
copied verbatim from the upstream source repository.

## Provenance

- **Source repo:** [`jgraph/drawio`](https://github.com/jgraph/drawio)
- **Upstream commit built:** `82af434539c3449d99275b91a91b6b99998a7d58` (v31.5.2)
- **How the output was produced:** copied the `src/main/webapp/` directory from a
  clean checkout of the upstream commit and deployed its *contents* to this
  repo's root (`index.html` lives at the root, not nested in a subfolder), plus
  this README and the upstream LICENSE.
- **Excluded:** `WEB-INF/` and `META-INF/` (servlet/App Engine deployment
  descriptors — `WEB-INF` also holds integration client secrets that must never
  be published).
- **Build date:** 2026-09-24
- The upstream README explicitly documents this deployment path: *"Fork this
  repository and publish to GitHub Pages for a fully functional editor
  (without integrations)."*

## What works / what doesn't

The full client-side diagram editor works without a backend: create, edit,
save (to device / browser storage), import and export diagrams — all locally
in the browser.

**Cloud-storage integrations are not available** in this static deployment:
Google Drive, OneDrive, Dropbox, GitHub/GitLab file access, and the server-side
export/PDF pipeline all require the upstream backend (`src/main/server`), which
is not included here.

## License

The draw.io source code is licensed under the
**[Apache License 2.0](LICENSE)** — see `LICENSE` (copied from the upstream
repository).

> **Important restriction on icons and stencils:** the icon sets, stencil
> libraries, and diagram templates included in this software, and any
> derivatives thereof, **may not be used as software assets in, distributed
> for use with, or incorporated into Atlassian products or products distributed
> through the Atlassian marketplace or plugin ecosystem**, without explicit
> written permission. This restriction does not apply to end-user diagram
> output (such as exported images or documents) created using this software.
> (Quoted from the upstream README; see upstream repository for the full text.)

## Trademark

draw.io is a registered EU trademark of draw.io Ltd / draw.io AG. This mirror
is an unofficial community deployment and is not affiliated with, endorsed by,
or sponsored by draw.io.
