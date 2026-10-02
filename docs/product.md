# Byro Adaptive LinkedIn Commenting — Product Definition

## User

A founder who wants to consistently participate in relevant LinkedIn conversations without spending significant time deciding what to comment and writing the comment manually.

## Problem

The founder wants to contribute to LinkedIn conversations, but generic AI comments can be inaccurate, repetitive, disconnected from the post, or unlike the founder's normal way of communicating.

The system should therefore help the founder decide whether a post is worth engaging with and propose a useful comment while keeping the founder in control of the final response.

## Product

A human-in-the-loop LinkedIn Comment Copilot.

The product takes a LinkedIn post as input and:

1. Decides whether the founder should engage.
2. Explains the reason for that decision.
3. Selects an appropriate commenting approach.
4. Generates a small number of comment suggestions using the founder's observed writing patterns.
5. Lets the founder approve, edit, or reject the suggestion.
6. Stores the human decision as feedback for future improvement.

## Comment Modes

The prototype will support four comment modes:

* Quick reaction
* Humorous / personal reaction
* Add an insight
* Ask a thoughtful question

The research examples show that comments are not always the same type: some are very short reactions, some are humorous or contextual, while others add a technical observation or ask a specific question.

## When the system should do nothing

The system should recommend no comment when:

* The post is not relevant to the founder.
* There is no useful contribution to make.
* A response would require an unsupported factual claim.
* The suggested response is generic or repetitive.
* The system is not confident enough to produce a useful response.

## Human Control

The AI may recommend and draft.

The founder makes the final decision.

The system must not automatically publish a comment to LinkedIn.

The founder can:

* Approve
* Edit
* Reject

## Success Signal

The primary success signal is whether the founder accepts or lightly edits a suggested comment rather than rejecting it.

Secondary signals include:

* Rejection rate
* Edit rate
* Comment-mode acceptance
* Reasons for rejection
* Repeated failure patterns

## Non-Goals

The prototype will not:

* Automatically post to LinkedIn.
* Automate a logged-in LinkedIn session.
* Scrape private LinkedIn data.
* Implement authentication.
* Implement billing.
* Build a full social-media management platform.
* Build production infrastructure.

## Core Risk

The riskiest assumption is that the system can produce comments that are both useful for the specific post and sufficiently aligned with the founder's actual commenting style.

The executable prototype should therefore focus on validating this assumption rather than building a large production system.

## Evidence Boundary

The current research contains public/synthetic examples of posts and comments collected for this evaluation. Company/brand posts are treated separately from personal commenting evidence rather than being automatically assumed to represent an individual's voice.
