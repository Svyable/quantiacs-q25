# GitHub Pages — Q25 Quantitative Research Lab

**Expected project URL:** https://svyable.github.io/quantiacs-q25/

The Pages site is the public-facing presentation layer for this repository. It should make the research legible without requiring someone to browse Python files or experiment manifests.

It is intended to surface:

- the frozen historical Top-10 research roster and evidence boundaries;
- the strategy/mechanism atlas;
- the research and testing methodology;
- the active frontier and new campaign summaries;
- cost, drawdown, turnover, causality and originality discipline;
- links back to the repository artifacts that are the source of truth.

The Pages site is **not** the evidence registry and is not allowed to turn PENDING work into measured work. Historical metrics must retain their dates and provenance; newly measured metrics belong in the repository first and may only be surfaced on Pages after the exact code/run is recorded.

## Deployment

The repository includes `.github/workflows/pages.yml`, which builds `docs/` with GitHub's Jekyll Pages action and deploys the resulting `_site` artifact.

For the first deployment, repository Pages must be enabled at:

**Settings → Pages → Build and deployment → Source: GitHub Actions**

After that, changes under `docs/**` on `main` automatically redeploy the site. The workflow may also be run manually with `workflow_dispatch`.

Repository visibility and the GitHub account/organization plan determine Pages visibility for a private source repository. Do not make this repository public merely to publish the site without an explicit decision to do so.

## Source of truth

The repository remains authoritative. Pages is a curated public research surface. Do not publish credentials, participant-bound Quantiacs results, private artifacts, or claims of contest approval.
