# Google Cloud setup: owner action required

Do this only when you are ready to begin the analytics/cloud phase. The local app does
not need Google Cloud.

## Expected cost posture

Use the Google Cloud trial if eligible and create a hard personal operating rule to
stay within the project's $100 total budget. Google Cloud budget alerts notify you;
they do not automatically cap all spending. Delete unused resources after testing.

## What you need to do

1. Sign in to Google Cloud with the account that will own the portfolio project.
2. Create a new project, for example `dataprep-ai-portfolio`.
3. Attach the free-trial billing account or another billing account.
4. In **Billing > Budgets & alerts**, create alerts at $10, $25, $50, and $80.
5. Select one region and keep storage, BigQuery, and compute in that region. `US` is
   the current SQL default; tell Codex before continuing if you choose another region.
6. Enable these APIs:
   - BigQuery API
   - Cloud Storage API
   - Cloud Run Admin API
   - Artifact Registry API
   - Cloud Build API
7. Create a service account named `dataprep-app`.
8. Do **not** download or commit a long-lived JSON key yet. The next implementation
   step should prefer local Application Default Credentials and workload identity for
   deployed services.
9. Record the project ID and chosen region (neither is secret).

## Stop and return with

- Google Cloud project ID
- selected region (`US` is simplest for the prepared BigQuery schema)
- confirmation that billing alerts and the listed APIs are enabled

Do not paste API keys, service-account keys, passwords, or billing details into chat or
GitHub. Once the three non-secret items above are ready, Codex can implement and test
the BigQuery writer, transformations, data-quality checks, dashboard queries, Docker
packaging, and Cloud Run deployment.
