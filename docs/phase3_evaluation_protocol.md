# Phase 3 Evaluation Protocol

## Purpose

Evaluate whether the Precision Teaching AI intervention improves learning outcomes
relative to static learning materials. Obtain institutional approval and informed
consent before collecting or analysing real student data.

## Conditions

- Control: conventional/static learning material.
- Experimental: diagnostic assessment, BKT learner model, personalized resources,
  adaptive practice, and the AI tutor.
- Optional ablation: adaptive learning without generative AI, subject to sample size.

Use a pre-test, learning intervention, and post-test. Do not use synthetic data for
research conclusions; generated project datasets are for development and testing only.

## Dataset and privacy

Analysis records use anonymized IDs and include group, topic, pre/post scores, gain,
normalized gain, time to mastery, attempts, initial/final mastery, recommendation
completion, AI session count, and `data_source`. Keep identifying data separately.

Teacher analytics omit private AI message content unless an approved institutional
policy explicitly permits access.

## Metrics

For scores expressed as percentages:

$$g = \frac{posttest - pretest}{100 - pretest}$$

Report pre-test, post-test, absolute gain, normalized gain, time to mastery, BKT
prediction accuracy/precision/recall/F1, recommendation completion rate, and expert
review rates for generated-content correctness, relevance, readability, difficulty
appropriateness, and errors. Measure usability with SUS separately from learning
outcomes.

## Analysis plan

Inspect distributions and study design assumptions before selecting tests. Use paired
tests for within-student pre/post comparisons; use independent tests or ANCOVA for
between-condition comparisons as appropriate. Report effect sizes and confidence
intervals alongside p-values. Do not invent results or interpret subjective survey
responses as proof of learning effectiveness.
