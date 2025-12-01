# Analyze POC Data

You are a data analysis expert for the PEA RE Forecast Platform.

## Task
Analyze the POC Data from `requirements/POC Data.xlsx` and provide insights.

## Instructions

1. **Load and Inspect Data**:
   - Read all sheets: Solar, 1 Phase, 3 Phase
   - Check data types, missing values, date ranges
   - Identify data quality issues

2. **Statistical Analysis**:
   - For Solar: Analyze irradiance patterns, temperature correlations, power output distribution
   - For 1 Phase: Analyze voltage patterns per prosumer, identify anomalies
   - For 3 Phase: Analyze phase balance, transformer load patterns

3. **Data Sufficiency Assessment**:
   - Calculate total data points per category
   - Identify gaps in time series
   - Recommend additional data needed for production ML models

4. **Output Requirements**:
   - Save analysis report to `docs/data-dictionary/poc-data-analysis.md`
   - Include visualizations recommendations
   - List data generation requirements for simulation

## Expected Output Format

```markdown
# POC Data Analysis Report

## Executive Summary
[Key findings]

## Data Overview
[Sheet-by-sheet breakdown]

## Quality Assessment
[Issues found]

## Recommendations
[What's needed for production]
```
