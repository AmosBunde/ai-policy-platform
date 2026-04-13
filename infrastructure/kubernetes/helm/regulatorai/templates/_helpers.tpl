{{/*
Common labels
*/}}
{{- define "regulatorai.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
{{- end }}

{{/*
Selector labels for a specific component
*/}}
{{- define "regulatorai.selectorLabels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end }}

{{/*
Pod security context (shared across all deployments)
*/}}
{{- define "regulatorai.podSecurityContext" -}}
runAsNonRoot: {{ .Values.podSecurityContext.runAsNonRoot }}
runAsUser: {{ .Values.podSecurityContext.runAsUser }}
runAsGroup: {{ .Values.podSecurityContext.runAsGroup }}
fsGroup: {{ .Values.podSecurityContext.fsGroup }}
seccompProfile:
  type: RuntimeDefault
{{- end }}

{{/*
Container security context (shared across all containers)
*/}}
{{- define "regulatorai.containerSecurityContext" -}}
readOnlyRootFilesystem: {{ .Values.containerSecurityContext.readOnlyRootFilesystem }}
allowPrivilegeEscalation: {{ .Values.containerSecurityContext.allowPrivilegeEscalation }}
capabilities:
  drop:
  {{- range .Values.containerSecurityContext.capabilities.drop }}
    - {{ . }}
  {{- end }}
{{- end }}

{{/*
Full image reference
*/}}
{{- define "regulatorai.image" -}}
{{- if .global.imageRegistry -}}
{{ .global.imageRegistry }}/{{ .image.repository }}:{{ .image.tag }}
{{- else -}}
{{ .image.repository }}:{{ .image.tag }}
{{- end -}}
{{- end }}
