# Canary Release Strategy for Abraxas Helm Chart

## Overview
This document describes how to implement canary releases for Abraxas deployments using the Helm chart.

## Canary Release Implementation

### Strategy
We'll implement a canary release strategy using:
1. Label-based routing (similar to blue-green)
2. Weight-based traffic splitting via Istio/Linkerd service mesh (if available)
3. Automated promotion based on metrics

### Values.yaml Additions
```yaml
# Canary release configuration
canary:
  # Enable canary release strategy
  enabled: false
  # Percentage of traffic to send to canary (0-100)
  trafficPercentage: 10
  # Canary image tag (defaults to main image tag if not set)
  imageTag: ""
  # Minimum readiness percentage for promotion
  minReadiness: 95
  # Required duration at minReadiness before promotion (minutes)
  promotionDelay: 10
```

### Deployment Template Modifications
```yaml
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "abraxas.selectorLabels" . | nindent 6 }}
      {{- if .Values.bluegreen.enabled }}
      color: {{ .Values.bluegreen.activeColor }}
      {{- end }}
      {{- if .Values.canary.enabled }}
      track: {{ if eq .Release.Name "canary" }}canary{{ else }}stable{{ end }}
      {{- end }}
  template:
    metadata:
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      labels:
        {{- include "abraxas.selectorLabels" . | nindent 8 }}
        {{- with .Values.podLabels }}
        {{- toYaml . | nindent 8 }}
        {{- end }}
        {{- if .Values.bluegreen.enabled }}
        color: {{ .Values.bluegreen.activeColor }}
        {{- end }}
        {{- if .Values.canary.enabled }}
        track: {{ if eq .Release.Name "canary" }}canary{{ else }}stable{{ end }}
        {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      serviceAccountName: {{ include "abraxas.serviceAccountName" . }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          image: "{{ .Values.image.repository }}:{{ .Values.canary.enabled .Values.canary.imageTag | default .Values.image.tag | default .Chart.AppVersion }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: {{ .Values.service.port }}
              protocol: TCP
          livenessProbe:
            httpGet:
              path: /health
              port: http
          readinessProbe:
            httpGet:
              path: /ready
              port: http
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          {{- with .Values.volumeMounts }}
          volumeMounts:
            {{- toYaml . | nindent 12 }}
          {{- end }}
      {{- with .Values.volumes }}
      volumes:
        {{- toYaml . | nindent 8 }}
      {{- end }}
{{- if .Values.autoscaling.enabled }}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {{ include "abraxas.fullname" . }}
  labels:
    {{- include "abraxas.labels" . | nindent 4 }}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {{ include "abraxas.fullname" . }}
  minReplicas: {{ .Values.autoscaling.minReplicas }}
  maxReplicas: {{ .Values.autoscaling.maxReplicas }}
  metrics:
    {{- if .Values.autoscaling.targetCPUUtilizationPercentage }}
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetCPUUtilizationPercentage }}
    {{- end }}
    {{- if .Values.autoscaling.targetMemoryUtilizationPercentage }}
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: {{ .Values.autoscaling.targetMemoryUtilizationPercentage }}
    {{- end }}
{{- end }}
```

### Installation Examples

#### Stable Release
```bash
helm install abraxas-stable ./abraxas \
  --namespace abraxas \
  --create-namespace
```

#### Canary Release
```bash
helm install abraxas-canary ./abraxas \
  --namespace abraxas \
  --set canary.enabled=true \
  --set canary.trafficPercentage=15 \
  --set canary.imageTag="4.0.3-canary.1" \
  --set fullnameOverride="abraxas-canary"
```

#### Service Mesh Traffic Splitting (if using Istio)
```yaml
# VirtualService for Istio traffic splitting
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: abraxas-vs
spec:
  hosts:
  - abraxas
  http:
  - route:
    - destination:
        host: abraxas-stable
        subset: stable
      weight: 85
    - destination:
        host: abraxas-canary
        subset: canary
      weight: 15
```

### Promotion Process
1. Monitor canary metrics (error rates, latency, throughput)
2. When metrics meet criteria for `promotionDelay` minutes:
   ```bash
   # Promote canary to stable
   helm upgrade abraxas-stable ./abraxas \
     --set image.tag=<canary_image_tag> \
     --reuse-values
   
   # Update stable deployment to new version
   # Optionally: scale down/remove canary deployment
   ```

### Rollback Process
```bash
# Rollback to previous stable version
helm rollback abraxas-stable <revision_number>

# Or manually specify previous image tag
helm upgrade abraxas-stable ./abraxas \
  --set image.tag=<previous_stable_tag> \
  --reuse-values
```

## Benefits
- Zero-downtime deployments
- Risk mitigation through gradual traffic shifting
- Easy rollback capability
- Metrics-based promotion decisions
- Compatible with existing monitoring and alerting

## Requirements
- Kubernetes 1.16+ (for proper label selectors)
- Optional: Service mesh (Istio, Linkerd) for advanced traffic splitting
- Monitoring system to track canary metrics