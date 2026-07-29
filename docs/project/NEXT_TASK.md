# Next Task

## Task ID

SETUP-001

## Track

SHARED

## Objective

Validate the dual-track repository structure and prepare a controlled import
of existing project artifacts.

## Permitted actions

- inspect repository files;
- inspect Python environments;
- identify missing governance documents;
- propose the shared artifact-import structure;
- propose deterministic verification tests;
- report inconsistencies.

## Forbidden actions

- do not train any model;
- do not generate held-out-event predictions;
- do not inspect held-out-event performance;
- do not change the frozen event inventory;
- do not invent Track B feature definitions;
- do not install additional packages;
- do not copy or modify raw project data;
- do not alter scientific protocols.

## Required outputs

Produce a written implementation plan containing:

1. repository inventory;
2. environment inventory;
3. missing-document inventory;
4. artifact-import plan;
5. shared partition-module plan;
6. deterministic test plan;
7. recommended next bounded task.

## Stopping conditions

Stop and report rather than infer when:

- a controlling artifact is missing;
- two project documents conflict;
- a data hash cannot be verified;
- a timezone or schema is ambiguous;
- a requested action would modify a frozen rule.
