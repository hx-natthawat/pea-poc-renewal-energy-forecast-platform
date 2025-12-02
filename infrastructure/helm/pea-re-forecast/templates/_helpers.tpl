{{/*
Expand the name of the chart.
*/}}
{{- define "pea-re-forecast.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "pea-re-forecast.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "pea-re-forecast.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "pea-re-forecast.labels" -}}
helm.sh/chart: {{ include "pea-re-forecast.chart" . }}
{{ include "pea-re-forecast.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "pea-re-forecast.selectorLabels" -}}
app.kubernetes.io/name: {{ include "pea-re-forecast.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "pea-re-forecast.databaseUrl" -}}
{{- if .Values.timescaledb.auth.existingSecret }}
{{- printf "postgresql://%s:$(DB_PASSWORD)@timescaledb:5432/%s" .Values.timescaledb.auth.username .Values.timescaledb.auth.database }}
{{- else }}
{{- printf "postgresql://%s:%s@timescaledb:5432/%s" .Values.timescaledb.auth.username .Values.timescaledb.auth.password .Values.timescaledb.auth.database }}
{{- end }}
{{- end }}

{{/*
Redis URL
*/}}
{{- define "pea-re-forecast.redisUrl" -}}
{{- printf "redis://redis:6379/0" }}
{{- end }}

{{/*
CORS Origins String
*/}}
{{- define "pea-re-forecast.corsOrigins" -}}
{{- join "," .Values.cors.origins }}
{{- end }}
