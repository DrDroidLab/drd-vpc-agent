# DRD VPC Agent — Helm Chart

This chart deploys the Doctor Droid VPC Agent (celery-beat + celery-worker + redis) and an optional restart CronJob into your cluster.

## Prerequisites

- `kubectl` and `helm` v3+ installed locally
- Cluster access with permission to create the namespace, ServiceAccounts, ClusterRole, ClusterRoleBinding, Deployments, and (optionally) a CronJob
- A `DRD_CLOUD_API_TOKEN` from <https://aiops.drdroid.io/api-keys>
- A populated `credentials/secrets.yaml` describing the connectors you want the agent to poll (see `credentials/credentials_template.yaml`)

## Quick start

From the repository root:

```bash
# 1. Create the namespace
kubectl create namespace drdroid

# 2. Apply your connector credentials (edit credentials/secrets.yaml first)
kubectl -n drdroid apply -f helm/credentials-secret.yaml

# 3. Install the chart
helm dependency update helm/
helm upgrade --install drd-vpc-agent helm/ \
  -n drdroid \
  --set global.DRD_CLOUD_API_TOKEN=<your-token>
```

Verify:

```bash
kubectl -n drdroid get pods
# drd-vpc-agent-celery-beat-…    1/1  Running
# drd-vpc-agent-celery-worker-…  3/3  Running
# redis-…                        1/1  Running
```

## Configuration via `values.yaml`

The chart is driven entirely by `helm/values.yaml`. Three things are now configurable per component:

1. **Image** — `repository`, `tag`, `pullPolicy`
2. **Image pull secrets** — global and/or per component, merged together
3. **Security context** — pod-level (`podSecurityContext`) and container-level (`securityContext`)

### Components

| Key | What it controls |
|---|---|
| `celery-beat` | Beat scheduler pod (1 main container + 1 init container) |
| `celery-worker` | Worker pod (3 main containers: scheduler, task-executor, asset-extractor + 1 init container) |
| `redis` | Redis broker pod |
| `autoUpdate` | The kubectl rollout-restart CronJob (only rendered when `autoUpdate.enabled=true`) |
| `global` | Settings shared across all components: `DRD_CLOUD_API_TOKEN`, `DRD_CLOUD_API_HOST`, `nodeSelector`, `tolerations`, `imagePullSecrets` |

### Using a private registry

You can mirror or self-host any of the four images. Point each component at your registry and provide a pull secret.

```bash
kubectl -n drdroid create secret docker-registry my-registry-pull \
  --docker-server=my-registry.example.com \
  --docker-username=… --docker-password=…
```

```yaml
# values.override.yaml
global:
  imagePullSecrets:
    - name: my-registry-pull   # applied to every pod in the chart

celery-beat:
  image:
    repository: my-registry.example.com/drd/drd-vpc-agent
    tag: 1.0.6
    pullPolicy: IfNotPresent
  initContainer:
    image:
      repository: my-registry.example.com/drd/busybox
      tag: "1.36"

celery-worker:
  image:
    repository: my-registry.example.com/drd/drd-vpc-agent
    tag: 1.0.6
    pullPolicy: IfNotPresent
  initContainer:
    image:
      repository: my-registry.example.com/drd/busybox
      tag: "1.36"

redis:
  image:
    repository: my-registry.example.com/drd/redis
    tag: 8-alpine
  imagePullSecrets:
    - name: dockerhub-mirror   # additional secret only for redis; merged with global

autoUpdate:
  image:
    repository: my-registry.example.com/drd/kubectl
    tag: latest
```

```bash
helm upgrade --install drd-vpc-agent helm/ \
  -n drdroid \
  -f helm/values.yaml \
  -f values.override.yaml \
  --set global.DRD_CLOUD_API_TOKEN=<your-token>
```

### Security context (PSP / Gatekeeper / Pod Security Standards)

The chart ships defaults that satisfy the common "must run as non-root" and "no privilege escalation" policies:

| Component | Default `runAsUser` | Reason |
|---|---|---|
| `celery-beat`, `celery-worker` | `33` | matches the `www-data` user the agent image chowns `/code` to |
| `redis` | `999` | matches the `redis` user baked into `redis:8-alpine` |
| `autoUpdate` (kubectl CronJob) | `1000` | non-root, no filesystem requirements |

If your policy is stricter (e.g. requires `runAsUser` inside a specific UID range), override per-component:

```yaml
celery-worker:
  podSecurityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
  securityContext:
    allowPrivilegeEscalation: false
    runAsNonRoot: true
    runAsUser: 10001
    readOnlyRootFilesystem: true
    capabilities:
      drop: [ALL]
```

If you build your own image with a different baked-in user, change `runAsUser` to match the UID that owns `/code` in your image. You can probe it with:

```bash
kubectl run uid-probe --rm -it --restart=Never --namespace drdroid \
  --image=<your-image> --command -- sh -c 'id www-data; ls -ld /code'
```

## Upgrades

`values.yaml` and any override files are the source of truth. To roll out a change:

```bash
helm upgrade drd-vpc-agent helm/ \
  -n drdroid \
  -f helm/values.yaml \
  -f values.override.yaml
```

The chart's pod template includes a `rollme` annotation pinned to deploy-time, so every `helm upgrade` triggers a rolling restart of the agent pods even when the image tag is `latest`. The `autoUpdate` CronJob (default: daily at 00:00 UTC) issues `kubectl rollout restart` against both deployments to pick up new `latest` images between releases.

## Troubleshooting

**Gatekeeper denies pod admission with `psp-pods-allowed-user-ranges`**
The chart's defaults set `runAsNonRoot: true` and a non-zero `runAsUser`. If your policy still denies, your cluster likely enforces a UID *range* — set `runAsUser` (and `runAsGroup` / `fsGroup`) to a value inside the allowed range under each component's `podSecurityContext` and `securityContext`.

**Container exits with `unable to open database file` / permission errors**
The `runAsUser` you've set doesn't match the UID that owns `/code` in the image. Probe the image (see snippet above) and adjust `runAsUser` to that UID.

**Image pull fails with `ImagePullBackOff`**
Either the image isn't present in your registry, or the pull secret isn't reachable from the pod's namespace. Confirm:
```bash
kubectl -n drdroid get secrets | grep -i pull
kubectl -n drdroid describe pod <pod>   # check the Events section
```
Make sure the secret named in `imagePullSecrets` exists in the same namespace as the release.

**Old pods stuck in CrashLoopBackOff after upgrade, blocking the new pod from scheduling**
Rolling-update strategy keeps the old pod alive until the new one is Ready. If the cluster is CPU-tight and the new pod is Pending, scale the deployment to 0 and back to 1:
```bash
kubectl -n drdroid scale deployment drd-vpc-agent-celery-worker --replicas=0
kubectl -n drdroid scale deployment drd-vpc-agent-celery-worker --replicas=1
```

## Uninstall

```bash
helm -n drdroid uninstall drd-vpc-agent
kubectl delete namespace drdroid    # only if you want to remove the credentials secret too
```
