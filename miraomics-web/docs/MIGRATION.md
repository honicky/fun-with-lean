# Migrating off the managed host (WordPress/Wix)

The current site is on a managed platform. This is a cutover plan to the new
S3 + CloudFront stack with zero/minimal downtime.

## 0. Before you touch DNS

- Stand up the new stack in AWS (`terraform apply`) and deploy the site via CI.
- Verify it on the raw CloudFront domain (set `route53_zone_id = ""` for a first
  pass to skip the custom-domain cert), or on a staging subdomain.
- Confirm forms work end-to-end: submit a test lead, check it lands in DynamoDB
  and that the notification email arrives.

## 1. Move DNS to Route53 (if not already)

1. Create a hosted zone for `miraomics.bio` in Route53.
2. Recreate existing records (MX/email, TXT/SPF/DKIM, any subdomains) — **don't
   forget email DNS**, or you'll break inbound mail.
3. At the registrar, point the nameservers at the Route53 zone.
4. Wait for propagation; verify with `dig NS miraomics.bio`.

Set `route53_zone_id` in `terraform.tfvars` and re-apply to get
`www.miraomics.bio` + `api.miraomics.bio` with managed TLS.

## 2. Content parity

The new pages cover Home, MiraTyper, Services, About, Contact, plus landing
pages. Port any case studies / blog content you want to keep into:

- Pages → add `src/pages/<name>.astro` (copy an existing page as a template).
- A blog → add a `blog` content collection mirroring `landing` (Markdown in,
  route out). Ask for this if you want it scaffolded.

## 3. Redirects (preserve SEO)

Map old URLs to new ones so inbound links and search rankings survive. Two
options:

- **CloudFront Function:** extend `modules/static-site/cf-rewrite.js` with a
  redirect map (301) for changed paths.
- **Static redirect pages:** add `src/pages/old-path.astro` with a meta-refresh
  + canonical to the new path.

List the old URLs (export from the current CMS or pull from Search Console) and
add them to the rewrite function.

## 4. Cutover

1. Lower TTLs on the apex/www records a day ahead.
2. Flip `www` and apex to the CloudFront alias (Terraform does this when
   `route53_zone_id` is set).
3. Watch CloudWatch + the dashboard for traffic landing on the new stack.
4. Keep the old host up read-only for a few days as a rollback.

## 5. Decommission

Once traffic and forms are confirmed on the new stack and email is unaffected,
cancel the managed subscription.
```
