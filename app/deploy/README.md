# OpenShift Deployment

## Deploy

```bash
# Edit secret.yaml
oc apply -f secret.yaml

# Update image path in deployment.yaml, then deploy
oc apply -f deployment.yaml
```

## Verify

```bash
oc get pods -l app=sast-ai-dvc
oc get route sast-ai-dvc
```

## Logs

```bash
oc logs -f deployment/sast-ai-dvc
```
