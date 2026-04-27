# JFrog Xray "Exposures" — Verified False Positives

This document records every Xray Exposures finding against the drd-vpc-agent image that was verified to be a false positive and the reason it cannot be resolved by a code change. Each entry is the justification text to attach to the corresponding Xray Ignore Rule.

Triage scope: findings against image built from `Dockerfile` with `requirements.txt` at branch `fix/jfrog-xray-security-violations`, confirmed with Trivy 0.69.3 (secrets scanner silent on every item below).

Every item here has been checked against the actual file contents inside the runtime image. None of them correspond to real credentials.

---

## 1. `awscli` — EKS token prefix constant

**Xray issue:** `EXP-1685-88216282`
**Path in image:** `/code/deps/awscli/customizations/eks/get_token.py:67`
**Flagged literal:**
```python
TOKEN_PREFIX = 'k8s-aws-v1.'
```

**What it is:** The AWS EKS signed-URL authentication protocol prefix. Every EKS cluster-authentication token produced by `aws eks get-token` (and by the equivalent logic in `aws-iam-authenticator` and `kubectl`'s EKS exec plugin) carries this literal prefix. It is the wire-format identifier that EKS control planes use to recognize the token format.

**Why it can't be removed or renamed:**
- Renaming the Python symbol has no effect — Xray flags the string literal itself.
- Changing the string value breaks EKS authentication: the server expects exactly `k8s-aws-v1.`. Any other value fails to authenticate.
- The same literal exists in `aws-iam-authenticator` (Go), in kubectl's EKS exec plugin, and in the AWS documentation. It is a public protocol constant, not a secret.

**Runtime dependency:** Imported at `drdroid_debug_toolkit/core/integrations/source_api_processors/eks_api_processor.py:8` (`from awscli.customizations.eks.get_token import TokenGenerator, TOKEN_EXPIRATION_MINS, STSClientFactory`). Removing or editing this file breaks the EKS connector.

**Disposition:** Ignore. Protocol identifier, not a credential.

---

## 2. `msal` — SAML 1.0 assertion URN

**Xray issue:** `EXP-1685-88216616`
**Path in image:** `/code/deps/msal/wstrust_response.py:38`
**Flagged literal:**
```python
SAML_TOKEN_TYPE_V1 = 'urn:oasis:names:tc:SAML:1.0:assertion'
```

**What it is:** An OASIS-registered URN identifying the SAML 1.0 assertion token type. Published in the SAML 1.0 core specification; used by WS-Trust message parsers to decide which token type was returned by a Security Token Service.

**Why it can't be removed or renamed:**
- The URN is normatively defined by OASIS — any replacement string makes msal unable to recognize legitimate SAML 1.0 responses.
- URN format happens to match a Python "secret"-style regex (long colon-delimited identifier), but it is a public namespace identifier registered at [docs.oasis-open.org](https://docs.oasis-open.org/security/saml/v1.0/).

**Runtime dependency:** `msal` is pulled in transitively by `azure-identity` which is used for Azure/AKS connector authentication. Its WS-Trust parser requires this constant to dispatch SAML 1.0 vs 2.0 responses.

**Disposition:** Ignore. Public OASIS URN, not a credential.

---

## 3. `msal` — WS-Security SAML Token Profile 1.1 URL

**Xray issue:** `EXP-1685-88216618`
**Path in image:** `/code/deps/msal/wstrust_response.py:42`
**Flagged literal:**
```python
WSS_SAML_TOKEN_PROFILE_V1_1 = "http://docs.oasis-open.org/wss/oasis-wss-saml-token-profile-1.1#SAMLV1.1"
```

**What it is:** The OASIS WS-Security SAML Token Profile 1.1 namespace URI (fragment `#SAMLV1.1`). Used by msal to advertise or recognize the token profile in WS-Trust SOAP headers.

**Why it can't be removed or renamed:** Same reasoning as item #2 — the URL is a standards-defined namespace identifier, not a secret. Replacing it breaks SAML 1.1 profile negotiation in WS-Trust exchanges.

**Runtime dependency:** Same as item #2 — used by the WS-Trust response parser in `msal`, required for Azure authentication paths that go through SAML-federated STS.

**Disposition:** Ignore. Public OASIS namespace URL, not a credential.

---

## 4. `kubernetes` client — CephFS volume `secret_file` field

**Xray issue:** `EXP-1685-88216308`
**Path in image:** `/code/deps/kubernetes/client/models/v1_ceph_fs_persistent_volume_source.py:40`
**Flagged literal:**
```python
openapi_types = {
    'monitors': 'list[str]',
    'path': 'str',
    'read_only': 'bool',
    'secret_file': 'str',           # ← flagged
    'secret_ref': 'V1SecretReference',
    'user': 'str'
}
```

**What it is:** An entry in the OpenAPI-generated `openapi_types` dictionary for the `V1CephFSPersistentVolumeSource` model. The string `'secret_file'` is the Kubernetes API field name for a path on the host where the CephFS authentication secret can be found. It is the attribute **name**, not a value — it maps this Python attribute to its `secretFile` JSON wire field.

**Why it can't be removed or renamed:**
- The dictionary is consumed by the kubernetes client's generic (de)serializer: the key `'secret_file'` must match the Python attribute name (`self._secret_file`) and the `attribute_map` value `'secretFile'` must match the JSON wire field. Changing either breaks (de)serialization of any CephFS PV in the cluster.
- This file is generated from the official Kubernetes OpenAPI spec — every version of the `kubernetes` Python client (verified from 26.x through 35.0.0) generates an identical `openapi_types` dict. Upgrading does not remove the literal.
- CephFS in-tree driver was removed from kubelet in K8s 1.31, but the `CephFSPersistentVolumeSource` *API type* remains defined for backward compatibility in the K8s OpenAPI surface, so the generated model file persists.

**Runtime dependency:** The `kubernetes` client is imported by the toolkit's EKS/GKE connectors (`drdroid_debug_toolkit/core/integrations/source_api_processors/{eks,gke}_api_processor.py`). The generic serializer walks every model file at import time, so deleting this file causes import-time errors in the client.

**Disposition:** Ignore. Kubernetes API field name, not a credential.

---

## 5. `kubernetes` client — RBD volume `secret_ref` field

**Xray issue:** `EXP-1685-88216602`
**Path in image:** `/code/deps/kubernetes/client/models/v1_rbd_volume_source.py:42`
**Flagged literal:**
```python
openapi_types = {
    'fs_type': 'str',
    'image': 'str',
    'keyring': 'str',
    'monitors': 'list[str]',
    'pool': 'str',
    'read_only': 'bool',
    'secret_ref': 'V1LocalObjectReference',   # ← flagged
    'user': 'str'
}
```

**What it is:** The `secret_ref` entry in the OpenAPI-generated `openapi_types` for `V1RBDVolumeSource`. Same class as item #4: a Python-to-JSON field name map, not a value.

**Why it can't be removed or renamed:** Same reasoning as item #4. Renaming breaks serialization of every RBD volume object returned by the K8s API. File is auto-generated from upstream OpenAPI spec and present in every kubernetes client version.

**Runtime dependency:** Same as item #4 — imported at module-load time via the kubernetes client's model registry.

**Disposition:** Ignore. Kubernetes API field name, not a credential.

---

## 6 & 7. `django.contrib.auth.forms` — `UserChangeForm` password labels

**Xray issues:** `EXP-1685-88216567`, `EXP-1685-88216568`
**Paths in image:**
- `/code/deps/django/contrib/auth/forms.py:143` (varies by Django minor version — in Django 5.2.13 the `label=_("Password")` lines are at 94, 149, 182, 443)
- `/code/deps/django/contrib/auth/forms.py:151` (same — help-text literals on the same forms)

**Flagged literals:**
```python
password = ReadOnlyPasswordHashField(
    label=_("Password"),
    help_text=_(
        "Raw passwords are not stored, so there is no way to see this "
        "user's password, ..."
    ),
)
```

**What they are:** Translatable UI strings on Django's built-in `UserChangeForm` (used by `django.contrib.admin` to render the user-edit page). `_("Password")` is a translatable label shown to admins; the help_text is the disclaimer below the password field.

**Why they can't be removed or renamed:**
- `label=_("Password")` is a displayed form-field label. Changing the value changes what admins see. More importantly, `_()` marks the string for i18n catalog lookup; altering the marker string breaks translations for every language the admin is rendered in.
- These strings are part of Django core (`django.contrib.auth` ships with Django itself). Every release of Django since 1.0 — including our pinned `Django>=5.2,<5.3`, currently 5.2.13 — contains the same literals.
- You cannot remove `django/contrib/auth/forms.py` without breaking `django.contrib.auth`, which is required by every Django project that uses the auth system — including drd-vpc-agent (which uses `djangorestframework-simplejwt` and `django-rest-auth`, both of which depend on `django.contrib.auth`).

**Runtime dependency:** `django.contrib.auth` is in `INSTALLED_APPS` implicitly via the auth-dependent packages in `requirements.txt`. Removing auth is not an option.

**Disposition:** Ignore. Translated UI labels inside the web framework, not credentials.

---

## Summary — disposition matrix

| # | Xray ID | Package | Why ignore | Fix-at-source viable? |
|---|---|---|---|---|
| 1 | EXP-1685-88216282 | `awscli` | AWS EKS protocol constant | No |
| 2 | EXP-1685-88216616 | `msal` | OASIS SAML 1.0 URN | No |
| 3 | EXP-1685-88216618 | `msal` | OASIS WS-Security URL | No |
| 4 | EXP-1685-88216308 | `kubernetes` | K8s API field-name map | No |
| 5 | EXP-1685-88216602 | `kubernetes` | K8s API field-name map | No |
| 6 | EXP-1685-88216567 | `Django` | i18n label in core framework | No |
| 7 | EXP-1685-88216568 | `Django` | i18n help_text in core framework | No |

Version bumps do not eliminate any of the seven — each literal is either a protocol constant, a standards-registered URN/URL, an auto-generated OpenAPI field-name map, or a core framework i18n string. All seven are still present in the latest available version of their respective packages.

Recommended action for all seven: create an Xray **Ignore Rule** per issue ID and paste the corresponding "Disposition" line above as the justification.

---

## What *was* resolved, for context

Separate from the seven above, the following Xray Exposures findings in `drdroid_debug_toolkit/core/integrations/source_managers/*_source_manager.py` have been fixed at source in the toolkit repository:

| File | Fix |
|---|---|
| `big_query_source_manager.py` | Example service-account JSON replaced with `<your-*>` placeholders |
| `gcm_source_manager.py` | Same |
| `gke_source_manager.py` | Same |
| `github_source_manager.py` | Example `ghp_...` PAT replaced with `<your-github-personal-access-token>` |
| `github_actions_source_manager.py` | Same |

These were genuine false positives (UI help-text `e.g. ...` examples) but removable because they were documentation strings, not protocol/API literals.

---

## 2026-04-22 rescan — new in-repo fixes (`.dockerignore`)

A follow-up rescan on JFrog tenant `trialwyikk8` against image `drd-vpc-agent:scan-clean2` confirmed that 10 in-repo secret findings from the prior scan are all resolved. The fix was a single change: adding a `.dockerignore` file that keeps non-runtime artifacts out of the image, plus clearing one telemetry value.

| Previous finding | Disposition |
|---|---|
| `Dockerfile:25:44` (`EXAMPLE_*_TOKEN` in sed scrub literals) | Dockerfile excluded from image via `.dockerignore` |
| `credentials/credentials_template.yaml:14,24,61,76,143` | `credentials/` excluded — template not needed at runtime |
| `drdroid-debug-toolkit/drdroid_debug_toolkit/credentials_example.yaml:20,30` | `**/credentials_example.yaml` excluded |
| `helm/values.local.yaml:2:3` | `**/*.local.yaml` excluded (and value cleared) |
| `network-mapper-helm/values.yaml:206` (`networkMapperApiKey`) | Value cleared; `network-mapper-helm/` also excluded from image |
| `drdroid-debug-toolkit/env.sh` (3 real creds) | Excluded via `drdroid-debug-toolkit/env.sh` and `**/env.sh` |

Secondary benefit: `drdroid-debug-toolkit/testing/lib/python3.12/site-packages/` was a full testing virtualenv being copied into the runtime image. Excluding `drdroid-debug-toolkit/testing` eliminated **3 Critical Python CVEs** that were detected against stale Django 4.1.4 / cryptography 46.0.1 pins inside that virtualenv. The production runtime uses pip-installed Django 5.2.13 / cryptography 46.0.7 which are not affected.

### Note on `drdroid-debug-toolkit/env.sh`

Worth flagging separately: the toolkit's `env.sh` contains values that look like real credentials (Azure client secret, GCP service account private key, Azure tenant/subscription IDs). These are excluded from the image now, but they still live on disk and, if committed in the toolkit's own git history, remain exposed. Recommend rotating and scrubbing from the toolkit repo regardless of this image fix.

---

## 2026-04-22 rescan — additional deps/* findings (same class as items 1–7)

The new tenant's secrets scanner surfaced a larger population of findings in third-party package source that fall into the same disposition categories as items 1–7 above. They are not new CVEs — they are additional matches of the same regexes against the same kind of content (protocol constants, K8s API field-name maps, Django i18n labels, package METADATA tokens).

| Family | Files (`/code/deps/...`) | Count | Same disposition as |
|---|---|---|---|
| K8s API field-name maps (OpenAPI-generated `openapi_types`) | `kubernetes/client/models/v1_*.py` — ceph_fs, rbd, csi, cinder, flex, iscsi, scale_io, storage_os, env_var, env_from, volume, volume_projection (both `*_volume_source` and `*_persistent_volume_source` variants) | 25+ | Items 4, 5 |
| Django `UserChangeForm` password labels / help_text | `django/contrib/auth/forms.py` lines 129, 130, 143, 151, 185, 186 | 6 | Items 6, 7 |
| msal WS-Trust SAML URNs | `msal/wstrust_response.py` lines 37, 38, 41, 42, 44; `msal/managed_identity.py:343` | 6 | Items 2, 3 |
| RFC 6749 OAuth docstring examples | `oauthlib/oauth2/rfc6749/parameters.py` (5); `requests_oauthlib/` (28) | 33 | Already partially scrubbed by `Dockerfile` sed; residual matches in docstrings. Safe to ignore as docstring-only. |
| Google OAuth/ADC scope and header constants | `google/*` (14) | 14 | Same as items 1–3: public protocol identifiers |
| Package `METADATA` / `RECORD` files (PKG-INFO auto-generated) | `*/METADATA`, `*/RECORD` | ~10 | Random-looking hashes in the `RECORD` file and URL-containing tokens in `METADATA` are auto-generated by `pip wheel`, not credentials |
| Misc singletons (`awscli`, `azure`, `PyMySQL`, `sqlalchemy`, `pydantic`, `pyjwt`, `redis`, `openai`, `datadog`, `websocket-client`, etc.) | one file each | ~10 | Same character — protocol constants or package metadata |

**Total deps/* secret findings in the 2026-04-22 rescan: 104. All false positives in the same classes as items 1–7.**

### Recommended handling on new JFrog tenant (`drdroid` / `trialwyikk8`)

The old tenant's `EXP-1685-88216*` Ignore Rules do not carry over. On the new tenant, the pragmatic options are:

1. **One broad ignore rule per package** (e.g., one rule for all `deps/kubernetes/client/models/v1_*_volume_source.py` matches, one for `deps/django/contrib/auth/forms.py`) with the category justification from this document. Smaller-scope than a single blanket rule, less churn than per-line rules.
2. **Path-prefix ignore rule for `/code/deps/`** with `secrets` scanner type, noting that all deps were installed via `pip install -r requirements.txt` in the builder stage and scrubbed via the Dockerfile's `sed` step where safe. This is the lowest-effort option and matches the practical reality that every `deps/` secret is a protocol constant, OpenAPI field name, i18n label, RFC example, or auto-generated packaging metadata — never a credential.

Either route, the justification text for each family is already written in items 1–7 and the table above.
