# Geopol Forecaster -- Project History and Background

## Organization

**Geopol Forecaster** was created by **IQT Labs**, the applied research division of **In-Q-Tel (IQT)**. In-Q-Tel is an independent, non-profit venture capital firm based in Tysons, Virginia, founded in 1999. Its mission is to identify and deliver cutting-edge technologies to the U.S. intelligence community (CIA, DIA, FBI, NGA, NSA, DHS, U.S. Cyber Command, and allied intelligence services in the UK and Australia).

IQT Labs (formerly Lab41) is IQT's hands-on technical research arm, focused on exploring how national security agencies can leverage emerging machine learning and AI capabilities.

- **Website**: https://www.iqt.org/
- **IQT Labs GitHub**: https://github.com/IQTLabs
- **Contact**: labsinfo@iqt.org

## Authors and Roles

| Name | Role | Affiliation |
|------|------|-------------|
| Daniel P. Hogan | Senior Data Scientist | IQT Labs (dhogan@iqt.org) |
| Andrea Brennen | Senior VP and Deputy Director | IQT Labs (abrennen@iqt.org) |

A follow-up article in *Studies in Intelligence* (December 2025) added three co-authors from the CIA's Directorate of Digital Innovation (DDI) Futures team: **Rachel Grunspan**, **Jessica D. Smith**, and **Elizabeth VanderVeen**.

## Original GitHub Repository

- **URL**: https://github.com/IQTLabs/geopol
- **Internal GitLab** (referenced in git history): `gitlab.iqt.org:labs/geopol_dev`
- **License**: Apache 2.0
- **PyPI**: https://pypi.org/project/llm-geopol/

The fork at `danielrosehill/geopol` was derived from `IQTLabs/geopol`.

## Academic Papers

### Primary Paper (arXiv preprint)

- **Title**: "Open-Ended Wargames with Large Language Models"
- **Authors**: Daniel P. Hogan, Andrea Brennen
- **arXiv ID**: 2404.11446
- **Submitted**: April 17, 2024
- **URL**: https://arxiv.org/abs/2404.11446
- **Category**: cs.CL (Computation and Language)
- **License**: CC BY-SA 4.0

The paper introduces Geopol Forecaster as an LLM-powered multi-agent system for automating qualitative (open-ended) wargames, as opposed to the quantitative games that prior AI automation had focused on. It describes the software architecture and demonstrates two case studies: an AI incident response tabletop exercise and a geopolitical crisis simulation.

### CIA Studies in Intelligence Article

- **Title**: "Geopol Forecaster Multi-Player AI System: Lessons from Human-AI Teaming in War Games"
- **Authors**: Andrea Brennen, Rachel Grunspan, Daniel Hogan, Jessica D. Smith, Elizabeth VanderVeen
- **Journal**: *Studies in Intelligence*, Vol. 69, No. 4 (Extracts)
- **Date**: December 2025
- **Publisher**: CIA Center for the Study of Intelligence (CSI)
- **URL**: https://www.cia.gov/resources/csi/studies-in-intelligence/studies-in-intelligence-vol-69-no-4-extracts-december-2025/snow-globe-multi-player-ai-system-lessons-from-human-ai-teaming-in-war-games

This article documents the collaboration between IQT Labs and the CIA's DDI Futures team, describing jointly designed games where human participants played alongside or against AI-simulated personas, demonstrating AI wargames as a testbed for human-AI teaming in intelligence work.

## Project Timeline

| Date | Milestone |
|------|-----------|
| Oct 16, 2023 | First commit on internal GitLab (`gitlab.iqt.org:labs/geopol_dev`) -- Dockerfile and initial scripts |
| Oct--Dec 2023 | Early development: OpenAI, Hugging Face, llama.cpp model backends; player/control architecture |
| Apr 4, 2024 | Apache 2.0 license added (preparing for open-source release) |
| Apr 16, 2024 | GitHub repository created at `IQTLabs/geopol` |
| Apr 17, 2024 | arXiv preprint submitted (2404.11446) |
| Apr--Sep 2024 | Continued development: model setup scripts, version updates, dependency refinements |
| Apr 2025 | Azure OpenAI support added |
| Sep 2025 | Internal GitLab and GitHub branches merged; agentic RAG implemented |
| Oct--Nov 2025 | YAML-based simulation mode, multi-game setup, advisor chat improvements |
| Dec 2025 | *Studies in Intelligence* article published (CIA/IQT collaboration) |
| Late 2025 | User-defined game mode and custom game YAML support finalized |

## Funding and Affiliations

No explicit grant or funding numbers are mentioned in the arXiv paper. However, the project is a product of **IQT Labs**, which is funded through In-Q-Tel's broader mission to serve the U.S. intelligence community. The December 2025 *Studies in Intelligence* article confirms direct collaboration between IQT Labs and the **CIA's Directorate of Digital Innovation (DDI) Futures team**.

In-Q-Tel's government partners include: CIA, DIA, FBI, NGA, NRO, NSA, DHS, U.S. Cyber Command, the Office of Strategic Capital, and the UK and Australian intelligence communities.

## IQT Labs -- Other Related Open-Source Work

IQT Labs maintains numerous open-source projects on GitHub (https://github.com/IQTLabs), spanning AI/ML, network security, and geospatial analysis:

- **TorchSig** -- signal processing ML toolkit based on PyTorch
- **FakeFinder** -- modular framework for evaluating deepfake detection models
- **Packet Cafe** -- automated network traffic analysis platform
- **BirdsEye** -- RL/RF-based localization of mobile radio frequency targets
- **GitGeo** -- discovering the geography of open-source software contributors
- **Viziflu** -- multi-model seasonal influenza forecast visualization
- **Software Supply Chain Compromises** -- community-maintained dataset of supply chain attacks
- **RFML** -- RF machine learning toolkit

These projects share a common theme of applying emerging ML/AI techniques to national security and intelligence problems.
