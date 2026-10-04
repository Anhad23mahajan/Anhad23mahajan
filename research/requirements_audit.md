# Requirements and Fact-Check Audit: Multimodal AI Hackathon 2026, Track A

Auditor: independent requirements + fact-check pass. Audit date: 2026-10-04 (Sunday).
Scope: Track A "Cardiovascular Risk Visualization & Prediction" (IIT Mandi, Devpost).

Sources read in full (image-rendered PDFs, transcribed by eye, 7 pages total):
1. `Track_A.pdf` (4 pages): Track A statement.
2. `Multimodal_AI_Hackathon_2026_-_Submission_Guidelines.pdf` (1 page).
3. `Problem_Statements.pdf` (2 pages): overview of Tracks A to D.

Confidence labels used below: HIGH (standard textbook/guideline fact, or stated verbatim in an official document), MEDIUM (I am fairly sure but it should be checked), UNVERIFIED (from memory, could be wrong, must be checked before it appears in any deliverable). No citation below has been looked up online (the sandbox cannot reach UCI, Kaggle, Devpost, publishers). Bibliographic items are listed only as "candidate, verify".

---

## 0. Executive summary

* The official text asks for five things at once: a leakage-safe ML pipeline (30%), a 3D coronary map (25%), explainability (20%), integration with live updates (15%), and clean reproducible engineering (10%). Plus four Devpost components and a 6-page document.
* The hard, binary (pass/fail) items are all in the Submission Guidelines and the "Expected Deliverables" list. A missed one (video private, README without run instructions, a teammate not added on Devpost, doc over 6 pages) is cheaper to lose than any model accuracy point. These are scheduled for 2026-10-12/13, not 10-14.
* The "multimodal" wording is satisfied by the track as written (heterogeneous clinical evidence plus 3D output). Do not add a fake or untrained image/ECG-signal input. Recommended instead: group features by modality and show per-modality contribution (Section 3).
* The 3D map is symbolic. The statement itself says features "should not be treated as direct anatomical coordinates" and RWMA gives "no direct pixel-level or 3D anatomical lesion map". The UI must say so in plain words (Section 3.3).
* The sandbox cannot download the dataset or any heart mesh, cannot reach YouTube/Devpost, and has no browser. Several deliverables are therefore human-only (Section 6).

---

## 1. Faithful transcription of the official requirements

### 1.1 Track A statement (verbatim content, condensed only where noted)

**Primer (context given to developers):**
* CAD and stenosis: stenosis is narrowing of a coronary artery, "typically caused by plaque buildup". "In the provided dataset, CAD is associated with at least 50% narrowing of one or more of the major coronary vessels."
* Three target vessels: LAD supplies "the front of the heart"; LCX supplies "the side and back of the heart"; RCA supplies "the right side and bottom of the heart".
* ML goal: "predict overall CAD status and the stenosis status of the LAD, LCX, and RCA using the available clinical features."
* Overall CAD status: provided "in addition to the individual vessel labels. A patient may have significant stenosis in one or more of the target vessels, while the overall CAD label represents the presence or absence of CAD according to the dataset definition."
* Clinical and ECG features: demographic, clinical examination, laboratory, ECG, echocardiographic features, including age, blood pressure, pulse rate, cholesterol, cardiac enzymes, ST Elevation, T Inversion, LVH, Region with RWMA. "These features are provided as inputs to the prediction models and should not be treated as direct anatomical coordinates."
* RWMA: echocardiographic finding of abnormal motion of a region of the heart wall. "It can be used as a clinical feature by the model, but it does **not** provide a direct pixel-level or 3D anatomical lesion map in this dataset."

**Challenge:** "Build an interactive 3D visualization system that predicts coronary artery disease and overall cardiac risk from patient physiological and clinical data, mapping predictions onto an interactive 3D human anatomical model."

**Context:** CVD is a leading cause of death; "raw numbers fail to give clinicians or patients an intuitive understanding of where and how pathology is developing inside the body."

**Requirements:**
1. Predictive Modeling: (a) train classification models to predict overall CAD status; (b) predict stenosis status for LAD, LCX, RCA; (c) use demographic, clinical examination, ECG, laboratory, echocardiographic features; (d) exclude LAD, LCX, RCA and Cath from model input features when predicting CAD or vessel-specific stenosis, to prevent target leakage; (e) evaluate with appropriate classification metrics (accuracy, precision, recall, F1-score, ROC-AUC).
2. 3D Visual Mapping: (a) render an interactive 3D human torso/heart model (Three.js, WebGL, React Three Fiber, or VTK.js); (b) dynamically update the color-code of individual coronary artery nodes (LAD, LCX, RCA) from predicted stenosis probabilities; (c) allow users to rotate, zoom, and select anatomical regions to inspect localized/vessel-specific risk detail.
3. Clinical Dashboard: (a) display predicted overall CAD status and vessel-specific stenosis probabilities alongside the 3D canvas; (b) provide an interpretable breakdown of why the model predicted a given risk score (e.g. SHAP or LIME); (c) display physiological measurements alongside their relative contribution to the overall prediction.
4. 3D models: (a) "You may use" open-source mesh files (.obj/.gltf) for rendering human anatomy.
5. Clinical Safety Disclaimer: "The UI must include clear, visible visual disclaimers indicating that predictions are for decision support / educational purposes only and not a substitute for formal diagnostic imaging."

**Expected Deliverables:** working web prototype (interactive 3D viewer integrated with ML backend); trained prediction pipeline (clean code and model weights for cardiac risk and multi-vessel stenosis classification); clinical explanation dashboard (prediction metrics, feature importances SHAP/LIME, patient physiological breakdowns); project documentation (dataset preprocessing, model architecture, 3D pipeline setup, usage instructions, evaluation results; **max. 6 pages**); demonstration video (**3-10 minute YouTube video** showing the working system, feature input workflow, 3D visualization interactions, technical implementation).

**Technical Considerations:** responsive 3D interaction in modern browsers "without requiring dedicated GPUs"; architecture "should support the addition of clinical features, prediction models, or anatomical structures without requiring a complete redesign"; "consistent correspondence between model outputs and the displayed LAD, LCX, and RCA anatomical structures".

**Evaluation Criteria:** Predictive Performance 30% (classification performance, risk estimation quality, validation methodology); 3D Visualization 25% (anatomical representation, spatial risk mapping, interactive visualization); Clinical Interpretability 20% (feature attribution quality, clarity of risk explanation, physiological factor breakdown); System Integration 15% (data pipeline, model-dashboard integration, real-time visualization updates); Technical Implementation 10% (architecture, code quality, reproducibility, use of public datasets and anatomical resources). Weights sum to 100%.

**Suggested resources:** Primary dataset: UCI "Extension of Z-Alizadeh Sani Dataset" (also on Kaggle); 303 patient records (demographics, vital signs, lab values, echo findings); ground-truth labels LAD, LCX, RCA stenosis plus overall CAD. 3D meshes: BodyParts3D (Database Center for Life Science); open-source .gltf/.glb/.obj heart models (e.g. Sketchfab, Three.js repositories, NIH 3D Print Exchange).

### 1.2 Submission Guidelines (verbatim content)

"Your Devpost submission must include all four components before the submission deadline":
1. Project description on the Devpost project page: what you built, the problem it solves, how it works.
2. Source code/documentation: link to a **public** GitHub repository with source code and documentation. The repository **must** include a README with setup instructions, prerequisites/dependencies, and instructions for running the project.
3. Demo video: **3 to 10 minutes** on YouTube. "Unlisted is fine. Private is not." Must show the project running and explain the approach. **English audio or English subtitles required.**
4. Team information: all members using their **real full names**. Every teammate must have a Devpost account and **must be added to the submission**. Members not added "will not appear on the project page and may not receive a certificate".

NOTE: teams are 1-4 people.

### 1.3 Problem Statements overview
Lists Tracks A to D (B flood mapping from space; C contrastive speech analytics; D personalized tutoring) with links to each track statement, the Submission Guidelines, and a "PRIZE POOL DISTRIBUTION" document. Nothing additional for Track A. **The prize pool document was not supplied to this audit**; someone on the team must read it (Section 2, A-9).

---

## 2. Numbered atomic requirements checklist

Legend: **M** = mandatory (the text says "must", or it is a stated component/deliverable), **S** = "should"/expected, **P** = permitted option, **W** = scored criterion (not pass/fail). The "Src" column gives the document: TA = Track A statement, SG = Submission Guidelines, PS = Problem Statements.

### 2.1 Submission (Devpost) requirements

| ID | Requirement | Type | Src |
|---|---|---|---|
| SUB-01 | The Devpost submission contains all four components (description, repo link, video, team info) before the deadline. | M | SG |
| SUB-02 | Devpost project description states what was built. | M | SG |
| SUB-03 | Devpost description states the problem it solves. | M | SG |
| SUB-04 | Devpost description explains how the solution works. | M | SG |
| SUB-05 | A link to a **public** GitHub repository is on the submission. | M | SG |
| SUB-06 | Repo contains source code. | M | SG |
| SUB-07 | Repo contains documentation. | M | SG |
| SUB-08 | README contains setup instructions. | M | SG |
| SUB-09 | README lists prerequisites/dependencies. | M | SG |
| SUB-10 | README contains instructions for running the project. | M | SG |
| SUB-11 | Demo video is on YouTube. | M | SG |
| SUB-12 | Video visibility is Public or Unlisted (never Private). | M | SG |
| SUB-13 | Video length is between 3:00 and 10:00 (target 6-8 min; avoid the edges). | M | SG, TA |
| SUB-14 | Video shows the project running (not slides only). | M | SG |
| SUB-15 | Video explains the approach. | M | SG |
| SUB-16 | Video has English audio or English subtitles. | M | SG |
| SUB-17 | Team information lists every member by real full name. | M | SG |
| SUB-18 | Every teammate has a Devpost account. | M | SG |
| SUB-19 | Every teammate is added to the submission on Devpost (verify they appear on the public project page). | M | SG |
| SUB-20 | Team size is 1-4. | M | SG |

### 2.2 Track A functional requirements

| ID | Requirement | Type | Src |
|---|---|---|---|
| TA-01 | Classification model(s) trained for overall CAD status. | M | TA 1a |
| TA-02 | Classification model trained for LAD stenosis. | M | TA 1b |
| TA-03 | Classification model trained for LCX stenosis. | M | TA 1b |
| TA-04 | Classification model trained for RCA stenosis. | M | TA 1b |
| TA-05 | Inputs span demographic, clinical examination, ECG, laboratory, echocardiographic features. | M | TA 1c |
| TA-06 | LAD, LCX, RCA and Cath columns are all excluded from the input features for every one of the four targets (including: the LCX and RCA labels are not inputs when predicting LAD, and so on). | M | TA 1d |
| TA-07 | Each of accuracy, precision, recall, F1, ROC-AUC is reported, for each of the four targets. | M | TA 1e |
| TA-08 | An interactive 3D human torso/heart model renders in the browser using Three.js, WebGL, React Three Fiber or VTK.js. | M | TA 2a |
| TA-09 | The color of the LAD, LCX and RCA nodes updates dynamically from predicted stenosis probabilities. | M | TA 2b |
| TA-10 | User can rotate the 3D model. | M | TA 2c |
| TA-11 | User can zoom the 3D model. | M | TA 2c |
| TA-12 | User can select an anatomical region and see localized/vessel-specific risk detail. | M | TA 2c |
| TA-13 | Predicted overall CAD status is displayed alongside the 3D canvas. | M | TA 3a |
| TA-14 | Vessel-specific stenosis probabilities are displayed alongside the 3D canvas. | M | TA 3a |
| TA-15 | An interpretable breakdown (SHAP or LIME) of why the model predicted a given risk score is shown. | M | TA 3b |
| TA-16 | Physiological measurements are displayed alongside their relative contribution to the overall prediction. | M | TA 3c |
| TA-17 | Open-source .obj/.gltf meshes may be used (optional; licence must be respected). | P | TA 4a |
| TA-18 | The UI shows clear, visible visual disclaimers: decision support / educational only. | M | TA 5 |
| TA-19 | The UI disclaimer states predictions are not a substitute for formal diagnostic imaging. | M | TA 5 |

### 2.3 Expected deliverables

| ID | Requirement | Type | Src |
|---|---|---|---|
| DEL-01 | Working web application with the interactive 3D viewer integrated with the ML backend (the viewer must call/use the real trained model, not canned numbers). | M | TA |
| DEL-02 | Trained prediction pipeline: clean code. | M | TA |
| DEL-03 | Trained prediction pipeline: model weights shipped (or reproducibly regenerable by one command), for cardiac risk and multi-vessel stenosis. | M | TA |
| DEL-04 | Clinical explanation dashboard shows prediction metrics. | M | TA |
| DEL-05 | Dashboard shows feature importances (SHAP/LIME). | M | TA |
| DEL-06 | Dashboard shows patient physiological breakdowns. | M | TA |
| DEL-07 | Project documentation exists, **at most 6 pages**. | M | TA |
| DEL-08 | Doc covers dataset preprocessing. | M | TA |
| DEL-09 | Doc covers model architecture. | M | TA |
| DEL-10 | Doc covers 3D pipeline setup. | M | TA |
| DEL-11 | Doc covers usage instructions. | M | TA |
| DEL-12 | Doc covers evaluation results. | M | TA |
| DEL-13 | Demo video (3-10 min YouTube) demonstrates the working system. | M | TA |
| DEL-14 | Demo video demonstrates the feature input workflow. | M | TA |
| DEL-15 | Demo video demonstrates the 3D visualization interactions. | M | TA |
| DEL-16 | Demo video covers technical implementation. | M | TA |

### 2.4 Technical considerations

| ID | Requirement | Type | Src |
|---|---|---|---|
| TC-01 | 3D interaction stays responsive in modern browsers without a dedicated GPU (test with integrated graphics / software rendering). | S | TA |
| TC-02 | Architecture lets a new clinical feature, a new prediction model, or a new anatomical structure be added without a complete redesign (config/schema-driven). | S | TA |
| TC-03 | Model outputs map consistently to the displayed LAD, LCX and RCA structures (no label swap, no left-right mix-up). | S | TA |

### 2.5 Evaluation criteria (scored; each row is a sub-criterion to be demonstrably addressed)

| ID | Criterion | Weight | Sub-criteria |
|---|---|---|---|
| EV-1 | Predictive Performance | 30% | classification performance; risk estimation quality (probability quality, i.e. calibration/Brier, not only accuracy); validation methodology (leak-free CV, held-out test, no tuning on test) |
| EV-2 | 3D Visualization | 25% | anatomical representation; spatial risk mapping; interactive visualization |
| EV-3 | Clinical Interpretability | 20% | feature attribution quality; clarity of risk explanation; physiological factor breakdown |
| EV-4 | System Integration | 15% | data pipeline; model-dashboard integration; real-time visualization updates |
| EV-5 | Technical Implementation | 10% | architecture; code quality; reproducibility; use of public datasets and anatomical resources |

### 2.6 Inferred best-practice items (not stated by organisers, but each protects a stated item)

| ID | Item | Protects |
|---|---|---|
| X-01 | Dataset citation and licence attribution in README, doc and UI footer. | EV-5, scholarly honesty |
| X-02 | Mesh licence and author attribution (in README and in-app credits), or a procedurally generated mesh with no third-party licence. | EV-5, TA-17 |
| X-03 | Fixed random seeds, pinned dependency versions (`requirements.txt`/lock file, Node version), one-command train and one-command run. | SUB-10, EV-5 |
| X-04 | The 6-page doc is also committed to the repo (PDF) and linked from README; attach on Devpost if an upload slot exists. The Guidelines do not say where the doc is submitted, so cover both. | DEL-07 |
| X-05 | Honest "symbolic map" caption, uncertainty display, and limitations section (single centre, n=303, referral population). | EV-2, EV-3, TA-18 |
| X-06 | On-screen team real names in video credits and in the README (matches Devpost). | SUB-17 |
| X-07 | Tag a release (e.g. `v1.0-submission`) at submission time; keep the repo public and unarchived through judging. | SUB-05 |
| X-08 | Cross-check an outputs sanity test: P(CAD) vs max vessel probability consistency (Section 4.4). | TC-03, EV-3 |

### 2.7 Open administrative items (A-)

* A-1: Confirm the exact deadline date, time and timezone on the Devpost Overview/Schedule tab (Section 7).
* A-2: Read the Devpost Rules tab: eligibility (IIT Mandi affiliation?), team rules, IP/licence of submissions, whether AI-assisted coding or external data/models must be disclosed, and whether the code may be committed after the deadline.
* A-3: Confirm on Devpost that Track A is selectable/selected (the form may have a track field).
* A-4: Read the "PRIZE POOL DISTRIBUTION" document (not supplied).
* A-5: Confirm whether the 6-page documentation is uploaded to Devpost (file upload/"Try it out" links) or only in the repo.
* A-6: Confirm whether a hosted live demo URL is expected (the Guidelines do not require one; recommended optional).
* A-7: Confirm whether the repo must be created by a team member under a specific account (not stated; any public repo link is accepted).
* A-8: Confirm certificate eligibility conditions (teammates added).

---

## 3. Ambiguities and risks in the requirements

### 3.1 The "multimodal" question

Facts from the official text: the hackathon is branded "Multimodal AI", but Track A's data is a 303-row table with demographic, symptom/examination, ECG-derived (binary findings such as ST elevation, T inversion, LVH), laboratory and echo-derived values (EF-TTE, RWMA). There are no images, raw ECG waveforms or audio in the suggested dataset. The scoring rubric contains no explicit "multimodality" line item.

Possible judge expectations: (a) none beyond the rubric (most likely, since the rubric is explicit and the track's own Primer says the features are the inputs); (b) a judge may look for evidence that several data types are fused and that the output is non-tabular (the 3D scene); (c) a minority might expect an image/signal input.

Assessment of adding an optional extra modality (ECG-signal or image upload):
* Recommendation: **do not add as a core feature; decline unless every mandatory item is done by 10-11.** Reasons: no labelled training data exists in the dataset for it, so any model would be untrained or fabricated, which damages EV-1 and honesty, and it competes for the same ~10 days as the 55%+ of score that depends on the 3D map and explanations.
* A cheap, honest alternative that earns the "multimodal" framing: **group features by modality** (Demographics and history; Symptoms and exam; ECG findings; Laboratory; Echocardiography) and show a per-modality contribution bar (sum of SHAP values within each group) beside the per-feature plot. This directly serves TA-16 (physiological breakdown) and EV-3, and lets the video say "fusion of five clinical evidence streams rendered as a spatial 3D output".
* If a stretch feature is added after everything else, it must be labelled demo-only and must not influence any displayed probability.

### 3.2 Other ambiguities (team decision needed)

| # | Ambiguity | Why it matters | Suggested resolution |
|---|---|---|---|
| Q1 | "Overall cardiac risk" (Challenge) vs "overall CAD status" (Requirements). | Two different things could be built (a separate risk score vs the CAD label's probability). | Define "overall cardiac risk" = model probability of the dataset's overall CAD label, say so in the UI and doc. Do not invent a 10-year risk score. |
| Q2 | "Multi-vessel stenosis classification" (Deliverables). | Might mean 3 independent binary heads, or a multilabel/multi-output model, or a count of diseased vessels. | Train per-vessel binary models (or a multi-output wrapper) and add a derived "vessels predicted stenotic: 0-3" indicator. |
| Q3 | "Predicted stenosis probabilities" colour the arteries. | Requires calibrated probabilities. n=303 is small. | Report Brier score and calibration plot; calibrate with sigmoid (Platt) inside the CV loop or show raw model score labelled "model-estimated probability, uncalibrated" if calibration is not defensible. |
| Q4 | Where documentation is submitted (not a Devpost component in SG). | Doc could be missed. | Commit a PDF in the repo, link it from README and the Devpost description (SUB/X-04). |
| Q5 | Does "model weights" require a file in the repo? | Retraining on the judge's machine might not match. | Ship the weights file (small), plus `train.py` that regenerates it deterministically. Prefer a portable format (ONNX, JSON coefficients, or skops) over a bare pickle with an unpinned scikit-learn version. |
| Q6 | 3D "nodes". | Segment-level colouring (proximal/mid/distal) would imply localisation the data cannot support. | One node (or uniformly coloured tube) per vessel. Segments, if drawn, must carry the same colour and be labelled "uniform; no segment-level prediction". |
| Q7 | Real-time: server or in-browser inference. | Hosting is not required, and a live server dependency is a demo risk. | Run inference locally via a FastAPI/Flask backend started by one command, with an optional in-browser fallback (exported coefficients/ONNX). Video is the primary evidence for judges. |
| Q8 | Which dataset version: original UCI "Z-Alizadeh Sani" vs the "Extension" named by the organisers. | Vessel-level labels (LAD/LCX/RCA) are stated as part of the suggested Extension version. Column names/encodings may differ. | Use the organisers' Extension version; record the exact file name and SHA-256 in the docs. |
| Q9 | Overall CAD vs the three vessels. | Overall label is "according to the dataset definition" and CAD may be set by stenosis in other vessels (left main, branches). A patient could be CAD-positive with all three target vessels negative, and the model's P(CAD) could be lower than its vessel maxima, which looks contradictory to a judge. | At download time, cross-tabulate Cath vs any(LAD,LCX,RCA). Document the result. In the UI add a one-line explanation when the display looks inconsistent. |

### 3.3 Presenting the symbolic 3D map honestly

Statement text that constrains the design: features "should not be treated as direct anatomical coordinates"; RWMA "does **not** provide a direct pixel-level or 3D anatomical lesion map". The labels are per-vessel yes/no for stenosis of at least 50%; there is no segment, lesion position, length, or plaque morphology information in the data.

Therefore the colour on a vessel means exactly one thing: the model's estimated probability that this patient has the dataset's "stenosis of this vessel" label. It does not show where a lesion is.

Recommended presentation rules:
1. Permanent caption on the canvas: "Schematic heart. Colour = model-estimated probability of the dataset's >=50% stenosis label for that vessel. Not an image of this patient; position along the vessel is not predicted."
2. Colour entire vessels uniformly. No hot spot, "plaque blob", stenosis narrowing animation, or marker on a particular segment.
3. Use a perceptually ordered, colour-blind-safe sequential scale (not a red/green alarm scheme) with a numeric label and a legend. Show the decision threshold used for the binary "predicted stenotic" tag; probabilities are not clinical thresholds.
4. Show uncertainty: cross-validated AUC/CI on the dashboard, and calibration caveats.
5. Draw non-target branches (left main, diagonals, obtuse marginals, PDA) in neutral grey as "context, not modelled", or omit them. Never colour branches by their parent's probability without saying so.
6. Include the dataset's referral-population caveat (every patient had been sent for angiography, about 70% were positive); probabilities are not population risk.
7. Words to avoid: "diagnoses", "detects blockage", "locates plaque/lesion", "scan". Words to use: "model-estimated", "dataset-defined", "educational", "schematic".
8. Use the same wording in the video narration at least once, in the README and in the doc.

### 3.4 Other risks hidden in the text

* The rubric weights **validation methodology** inside the 30%. Small n and a four-target problem invite optimistic reporting. A judge will probe for leakage (TA-06) and for tuning on the test set.
* "Real-time visualization updates" (EV-4) means that changing an input must visibly recolour the arteries without a page reload, in under about a second. Pre-render nothing.
* The rubric says "use of public datasets and anatomical resources" (EV-5): citation and licences are scored; do not take a mesh without a licence.
* The Clinical Interpretability line is not bolded in the PDF; treat it as a full 20% criterion.
* The statement says LAD supplies "front", LCX "side and back", RCA "right side and bottom". These are simplifications; see Section 4.1 for a correct and consistent version you can use.

---

## 4. Domain fact-check

### 4.1 Coronary anatomy

| Claim | Confidence | Notes |
|---|---|---|
| The left main coronary artery (LM/LMCA) arises from the left aortic sinus, is short (about 1 to 2 cm in many hearts), and bifurcates into LAD and LCX. A third branch, the ramus intermedius, appears in a minority of people (trifurcation). | HIGH | LM is not a target in this dataset (no LM label known; check columns). |
| LAD runs in the anterior interventricular groove toward the apex. Branches: septal perforators (anterior two-thirds of the interventricular septum) and diagonals (D1, D2; anterolateral wall). Territory: anterior wall of the left ventricle, anterior septum, apex. | HIGH | "Front of the heart" in the statement is a fair simplification. |
| LCX runs in the left atrioventricular (AV) groove, curving around to the back of the heart. Branches: obtuse marginals (OM1, OM2; lateral wall), left atrial branches, and in left-dominant hearts the posterior descending artery (PDA) and posterolateral branches. Territory: lateral and posterolateral LV wall. | HIGH | Seen from the front, most of the LCX is hidden behind the heart; the viewer must rotate, so show a "rotate to see" hint or an inset. |
| RCA arises from the right aortic sinus and runs in the right AV groove. Branches: conus branch, SA nodal artery (RCA in roughly 60% of people, LCX in roughly 40%), acute (right) marginal branches, AV nodal artery, then PDA (when right-dominant) and posterolateral branches. Territory: right ventricle, inferior (diaphragmatic) wall, posterior third of the septum, AV node. | HIGH (SA nodal percentages: MEDIUM) | "Right side and bottom" is a fair simplification. |
| Dominance is defined by which artery gives rise to the PDA and reaches the crux (where the AV groove meets the interventricular groove). Right-dominant in the large majority (commonly quoted 70-85%), left-dominant about 8-15%, co-dominant about 5-10%. | HIGH (qualitative); MEDIUM (percentages vary by study) | Dominance is **not** in the dataset. Draw the typical right-dominant schematic and label it "typical schematic". |
| In an anterior view the patient's right is on the viewer's left; the apex points down, left (viewer's right) and forward. | HIGH | Common implementation bug: mirrored scene. Add a TC-03 test that the RCA mesh is on the viewer's left in the default view. |
| How to depict: a schematic coronary tree drawn as tubes along smooth 3D curves on a heart-shaped surface (LAD down the anterior groove, LCX along the left AV groove and around the back, RCA along the right AV groove), with node names matching the model's target keys exactly (`LAD`, `LCX`, `RCA`). | HIGH (design recommendation) | Procedural generation (for example `TubeGeometry` along `CatmullRomCurve3`) avoids licence problems and guarantees the names exist. |

### 4.2 Stenosis threshold: dataset versus clinical convention

* The dataset (and the Track A statement) label a vessel "stenotic" and CAD positive at **at least 50% diameter narrowing** on catheterisation. HIGH (stated verbatim in the Track A statement; matches the dataset papers' definition as I recall).
* Clinical convention: for **left main**, 50% or more is generally considered significant. For other major epicardial arteries, **70% or more** is the conventional "obstructive" threshold on angiography (the 2021 AHA/ACC chest pain guideline defines obstructive CAD as at least 70% in a major epicardial vessel or at least 50% in the left main). HIGH. Intermediate lesions (50-69%) are often assessed functionally (FFR/iFR); an FFR of 0.80 or less is the classic functional cut-off. MEDIUM-HIGH. CT-based reporting (CAD-RADS) also uses 50% and 70% bands. MEDIUM.
* Consequence: the dataset's positive class includes moderate lesions that many clinicians would not treat. The UI and doc should say "stenosis >=50% (dataset definition)" and never "blocked artery" or "needs a stent". Interpreting "positive" as "obstructive" overstates severity.
* Also note: angiographic percent stenosis is visually estimated, has inter-observer variability, and the dataset does not give lesion location along the vessel.

### 4.3 Terms

| Term | Meaning | Confidence |
|---|---|---|
| Cath | Cardiac catheterisation, here invasive coronary angiography, the reference standard from which the dataset's CAD label (and vessel labels) come. In the dataset it is the target column (values like "Cad"/"Normal"), which is why it must be excluded from the inputs. | HIGH (meaning); MEDIUM (exact value strings) |
| ST elevation | ECG finding of the ST segment above baseline; classically acute transmural ischemia (STEMI) but also pericarditis, early repolarisation, LV aneurysm, etc. Not specific for stable CAD. | HIGH |
| ST depression | ST segment below baseline; subendocardial ischemia, also drugs/electrolytes/LVH strain. (In the dataset as a separate column.) | HIGH |
| T inversion | Inverted T waves; ischemia, prior infarct, LVH strain, many non-cardiac causes. Nonspecific. | HIGH |
| LVH | Left ventricular hypertrophy (here as an ECG voltage-criterion finding); usually from long-standing hypertension, aortic stenosis, cardiomyopathy. Raises cardiovascular risk; not itself a coronary lesion. | HIGH |
| RWMA | Regional wall motion abnormality on echo (hypokinesia, akinesia, dyskinesia) in part of the LV wall; may follow ischemia or infarction in a coronary territory, but territories overlap and vary with dominance and collaterals. The dataset column "Region RWMA" is, as I recall, a small integer (0 to 4); my recollection is that it counts affected regions rather than naming one. Check the column values before describing it. | HIGH (meaning); UNVERIFIED (column coding) |
| EF-TTE | Ejection fraction measured by transthoracic echocardiography, in percent. Normal LVEF is roughly 55-70% (50% or more is usually regarded as preserved). | HIGH |
| Other columns (from memory of the original UCI table) | DM diabetes mellitus; HTN hypertension; FH family history; CRF chronic renal failure; CVA cerebrovascular accident; DLP dyslipidaemia; BP blood pressure; PR pulse rate; BBB bundle branch block; VHD valvular heart disease; FBS fasting blood sugar; CR creatinine; TG triglycerides; LDL/HDL; BUN; ESR; HB haemoglobin; K and Na; WBC; Lymph; Neut; PLT; LowTH Ang low-threshold angina; Function Class. | MEDIUM: read the actual header row of the downloaded file |
| Typical risk factors | Age, male sex, hypertension, diabetes, dyslipidaemia (high LDL), smoking, family history of premature CAD, obesity, chronic kidney disease, sedentary lifestyle. | HIGH |

Because "Region RWMA" and EF-TTE are downstream imaging findings of cardiac injury and are strongly associated with the label, they will probably be among the top SHAP features. This is not a statement-defined leakage (only LAD/LCX/RCA/Cath are excluded) but the doc should discuss it and not present the model as a screening tool for the general public.

### 4.4 The Z-Alizadeh Sani dataset

| Claim | Confidence |
|---|---|
| Collected at Shahid Rajaei Cardiovascular, Medical and Research Center, Tehran, Iran. | HIGH (as I recall it from the original papers); confirm on the UCI page |
| 303 patients, of whom 216 had CAD and 87 were normal by angiography (about 71% positive). | MEDIUM-HIGH (the 303 is in the Track A statement; the 216/87 split is as I recall it, verify) |
| Patients were referred for suspected CAD (elective angiography), i.e. a high-pretest-probability population, not the general public. | MEDIUM-HIGH |
| About 54 features in four groups (demographic, symptoms and examination, ECG, laboratory and echo) plus a label. The count quoted varies (54-56) between the original and extension versions. | MEDIUM |
| UCI id 412 is the original "Z-Alizadeh Sani" entry. The "Extension of Z-Alizadeh Sani Dataset" (the one the organisers name) is a separate, later UCI entry (I believe a different id in the 900s, number not verified). | MEDIUM for id 412; UNVERIFIED for the extension's id |
| Donors/creators: Roohallah Alizadehsani, Zahra Alizadeh Sani, Mohamad Roshanzamir (and possibly others). | UNVERIFIED: copy the donor list from the UCI page |
| Licence: UCI datasets published in the current format generally state **CC BY 4.0**, which permits copying and redistribution with attribution. I believe this applies but have not seen the page. A Kaggle re-upload may carry a different licence and uploader terms. | UNVERIFIED: read the UCI "licence" line; prefer the UCI copy |
| CAD is defined as at least 50% narrowing of a major vessel; non-CAD patients are labelled "Normal". | HIGH (stated in Track A) |
| Citation requested: whatever the UCI page "Cite/Citation" block shows. I do not reproduce a reference here. Candidate related papers I recall, each needing verification of authors, venue, year, pages, DOI before use: (1) Alizadehsani et al., "A data mining approach for diagnosis of coronary artery disease", Computer Methods and Programs in Biomedicine (2013); (2) Alizadehsani et al., "Coronary artery disease detection using computational intelligence methods", Knowledge-Based Systems (2016); (3) Alizadehsani et al., "Non-invasive detection of coronary artery disease in high-risk patients based on the stenosis prediction of separate coronary arteries", Computer Methods and Programs in Biomedicine (2018). | UNVERIFIED (existence MEDIUM; details not checked) |

Checklist to run when the file is in hand (human downloads; any machine can run it):
1. Row count equals 303, no duplicate rows, record SHA-256.
2. Print column names; confirm that LAD, LCX, RCA, Cath (and any left-main, "Cad" or other leakage-like columns) exist and drop every one of them from X.
3. Cross-tabulate Cath against any(LAD, LCX, RCA) (Q9).
4. Class balance per target (do not quote prevalence figures from this audit).
5. Check missing values, categorical encodings (string "Y"/"N", "Male"/"Fmale" spellings, if present), and the coding of Region RWMA.
6. Hunt for proxy leakage: any column that looks like a procedure outcome or a vessel-related field.
7. Confirm the licence line and copy the citation text.

### 4.5 Modelling facts worth saying correctly

* With n=303, accuracy from a single split has a wide interval (a +/-1 patient change is about 0.3 points on the full set, and test sets of about 60 patients swing several points). Use repeated stratified K-fold (for example 5x10 or 10x5), nested CV for tuning, report mean and standard deviation (or bootstrap CI), keep any scaler/imputer/feature selector inside the pipeline so it is fitted only on training folds. HIGH.
* Report ROC-AUC and also PR-AUC/Brier for the vessel targets where classes are imbalanced. HIGH.
* SHAP: `TreeExplainer` is exact and fast for tree ensembles; `LinearExplainer` for logistic regression. LIME is slower and less stable. Note SHAP explains the model, not causation. HIGH. Package `shap` is installable from PyPI in the sandbox (version 0.51.0 visible); scikit-learn and pandas are not preinstalled in the sandbox but are installable from PyPI.
* A calibration wrapper (`CalibratedClassifierCV`) can change how SHAP must be applied (explain the base model or the wrapped function). Decide early.

### 4.6 Medical-safety and regulatory wording

Facts: software that is intended to diagnose or treat can be regulated as a medical device (for example under India's Medical Devices Rules 2017/CDSCO, the US FDA's software-as-a-medical-device and clinical decision support policies, EU MDR). MEDIUM (the principle is HIGH; exact section numbers deliberately not cited). The safe position is a clearly stated **educational, non-clinical intended use**, no claim of accuracy for any individual, and no real patient data entry. The statement itself requires a visible disclaimer (TA-18, TA-19).

**Recommended UI banner (always visible, short, never dismissible permanently):**

> EDUCATIONAL RESEARCH PROTOTYPE. NOT A MEDICAL DEVICE. Not for diagnosis, treatment or any clinical decision. Predictions are statistical outputs of models trained on 303 angiography-referred patients from one hospital and are no substitute for formal diagnostic imaging (such as coronary angiography or CT angiography) or a qualified clinician.

**Recommended first-load modal / "About and limitations" panel (long form):**

> This tool is a hackathon prototype built for decision-support demonstration and education only. It is not a medical device, has not been cleared or approved by any regulatory authority (including CDSCO, FDA or EU notified bodies), and must not be used to diagnose, rule out, monitor or treat any condition. The 3D heart is a schematic: vessel colours show a model's estimated probability that the dataset's label "stenosis of at least 50%" is positive for that artery. They do not show where a narrowing is, how severe it is, or what is happening in your own arteries. The model was trained on 303 patients who were referred for coronary angiography at a single centre (Shahid Rajaei Cardiovascular Medical and Research Center, Tehran), so its probabilities do not describe the general population, and performance on other populations is unknown. The dataset's threshold (at least 50% narrowing) differs from the usual clinical definition of obstructive disease in most vessels (at least 70%). Do not enter identifiable personal health information. If you have symptoms, or are worried about your heart, contact a qualified clinician or emergency services.

Placement (all of them): persistent banner on the main screen; the 3D canvas overlay corner text (so that screenshots carry it); modal on first load requiring "I understand"; README top; documentation page 1 and the limitations section; Devpost description; the first and last 10 seconds of the video (spoken and on screen). Also: no real PHI is collected (inputs are processed in memory and not stored/logged), and the only dataset used is the public de-identified one.

---

## 5. Environment facts (what this sandbox can and cannot do)

Probed on 2026-10-04 with plain HTTPS requests through the provided proxy (no bypass attempted):

| Host | Result | Consequence |
|---|---|---|
| pypi.org | reachable (HTTP 200) | `pip install` of scikit-learn, xgboost, lightgbm, shap, pandas, fastapi, uvicorn, onnx etc. works. `shap` 0.51.0 and `ucimlrepo` 0.0.7 confirmed downloadable. |
| registry.npmjs.org | reachable | `npm install` of three, vite, react, @react-three/fiber, @react-three/drei works. `three` 0.186.1 (MIT) confirmed. |
| conda.anaconda.org | reachable (redirect) | conda packages possible. |
| raw.githubusercontent.com | reachable (redirect) | Only useful if someone gives the exact URL of a file in a public repo. |
| api.github.com | reachable, but **repo-scoped only**: a search endpoint call returned HTTP 403 ("sessions are bound to their configured repositories"). | The sandbox cannot discover dataset mirrors or mesh repos via GitHub search, and cannot create a new repository. |
| archive.ics.uci.edu, www.kaggle.com, devpost.com, huggingface.co | blocked (connection failed) | Dataset cannot be downloaded here. Devpost page cannot be read here. |
| www.youtube.com, cdnjs.cloudflare.com, cdn.playwright.dev | blocked | Cannot verify the YouTube upload or fetch browser binaries via the Playwright CDN. Do not depend on cdnjs for the app (bundle dependencies from npm). |
| Others named in the brief (sketchfab, Google Drive) | not retested individually; treated as blocked per the brief | |

Additional facts found:
* The npm `three` package tarball contains **no .glb/.gltf/.obj files and no models folder**, so a heart mesh cannot be obtained from it. A shallow `npm search` for heart/3D/gltf returned only generic glTF tooling, no anatomical heart asset (not exhaustive).
* `ucimlrepo` (PyPI) installs here but fetches from UCI, which is blocked; on the team's own machines it would work and is a convenient reproducibility hook (needs the correct dataset id; verify it).
* No browser (Chromium/Firefox) is installed here; Node 22.22, Python 3.11, and ffmpeg are available. WebGL rendering, screenshots, and visual QA of the 3D scene therefore **cannot be done in the sandbox** by default. Possible but unverified route: an npm-packaged Chromium build (for example the `@sparticuz/chromium` package, which bundles a binary in the registry tarball) with software GL; treat as UNVERIFIED and low priority. Logic can be tested headlessly (Vitest/Jest for the mapping from probability to colour, scene-graph node names, API contract tests).
* The working repo here (`/home/user/Anhad23mahajan`) is the author's GitHub **profile README repo**, bound to this session. It is not the right home for the hackathon project (judges would land on a profile page). The submission repo should be a new dedicated public repo created by a human.

### 5.1 What the team cannot complete from inside the sandbox (human actions)

| # | Human action | Needed for |
|---|---|---|
| H1 | Download the UCI "Extension of Z-Alizadeh Sani" CSV/XLSX in a browser (or `ucimlrepo` on a local machine); read the UCI licence and citation block; record the file name, SHA-256 and the dataset id; place the file in the repo (only if the licence permits redistribution) or document the download step. | TA-01..07, X-01 |
| H2 | Decide mesh: (a) procedural heart (recommended, no download), or (b) download from BodyParts3D / Sketchfab / NIH 3D Print Exchange in a browser, check each model's own licence, convert to .glb, and keep file size small (a few MB). | TA-08, TA-17, X-02 |
| H3 | Create the **public** GitHub repository, push the code, set the About description/topics, add a licence file for the code, and verify the repo opens while logged out. | SUB-05..10 |
| H4 | Clone the repo fresh on a clean machine/Codespace and follow the README verbatim, including on a laptop with integrated graphics. | SUB-10, TC-01 |
| H5 | Record the demo video (screen recording tool of choice) with English narration, add burned-in or uploaded English subtitles/captions. | SUB-14..16 |
| H6 | Upload to YouTube as **Unlisted** (not Private); check the duration is 3:00-10:00; open the link in an incognito window; check captions render. | SUB-11..13 |
| H7 | Each teammate creates/confirms a Devpost account; one person starts the project and adds every teammate; all use real full names; confirm they appear on the public project page. | SUB-17..19 |
| H8 | Fill the Devpost description (what, problem, how); paste repo and video links; select Track A (if a field exists); submit and verify the status says "Submitted", not "Draft". | SUB-01..05 |
| H9 | Confirm the deadline time and timezone and read the Rules tab (A-1, A-2). Read the prize document (A-4). | all |
| H10 | Visual QA of the 3D scene in at least two browsers (Chrome and Firefox or Edge), including a no-discrete-GPU machine. | TC-01, EV-2 |
| H11 | Export the 6-page doc as PDF, check page count is 6 or fewer, commit it. | DEL-07 |
| H12 | Check the Devpost Rules for any AI-assistance disclosure and for team eligibility. | A-2 |

---

## 6. Risk register (ordered by likelihood x impact; scale 1-5 each)

| Rank | Risk | L | I | Score | Mitigation |
|---|---|---|---|---|---|
| 1 | Scope creep and time overrun against about 10 days (3D, ML, SHAP, integration, doc, video all needed). | 4 | 4 | 16 | Freeze features on 10-10; vertical slice by 10-06 (even with a toy model); no extra modality; cut order: LIME (keep SHAP), segment views, hosted demo. Daily 15-minute check against this register. |
| 2 | Target leakage or optimistic validation (preprocessing before split, tuning on test, a leakage-like column left in, Cath/vessel labels used as inputs for another target). | 3 | 5 | 15 | Single `FEATURE_BLACKLIST` constant used everywhere; unit test that asserts the four names are absent from X for all four targets; sklearn Pipelines; nested CV; fixed seed; documented. |
| 3 | Devpost administration failure: teammate not added, wrong names, draft left unsubmitted, link private. | 3 | 5 | 15 | Complete the Devpost team setup on 10-05 (not 10-13); screenshot the public project page; submit a full version by 10-13; edit afterwards if needed. |
| 4 | Small-n high-variance metrics and poor probability calibration, undermining the 30% criterion and the colour semantics. | 5 | 3 | 15 | Repeated stratified CV with confidence intervals; Brier and calibration plot; simple strong baselines (regularised logistic regression, random forest, gradient boosting); report honestly; avoid chasing a number. |
| 5 | Video non-compliance (private, under 3 or over 10 minutes, no English, not showing the app running, audio unusable). | 3 | 5 | 15 | Script and timer on 10-10; record 10-11; upload and verify in incognito 10-12; hard target 6-8 minutes; captions reviewed by a human. |
| 6 | 3D mesh unavailable, wrongly licensed, no coronary arteries on it, or too heavy for non-GPU laptops. | 4 | 3 | 12 | Default to a procedural heart and coronary tubes (full control of node names, tiny file); optional downloaded mesh only as a skin with attribution. Test on integrated graphics; cap pixel ratio; no heavy post-processing. |
| 7 | Dataset version/column mismatch (extension vs original; encodings; a missed leakage column). | 3 | 4 | 12 | Section 4.4 checklist on day 1; write a schema file listing every column with type and group. |
| 8 | Reproducibility failure on a judge's machine (unpinned versions, a pickle that does not load, Node version, absent data file). | 3 | 4 | 12 | Pin versions; ship portable weights (ONNX/JSON or a pinned-version joblib); `make setup`, `make train`, `make run`; test from a fresh clone; CI optional. |
| 9 | Overclaiming or misleading symbolic mapping; weak or hidden disclaimer. | 3 | 4 | 12 | Section 3.3 rules; Section 4.6 text; a pre-submission "claims review" by a teammate who reads the UI, video script and Devpost text. |
| 10 | Deadline misread (time or timezone). | 2 | 5 | 10 | Confirm on the Devpost Schedule tab on 10-04; plan to submit 24 hours early. |
| 11 | Rules not read: AI-assisted work, team/eligibility, post-deadline commits. | 2 | 4 | 8 | Read the Rules tab on 10-04, disclose AI assistance if required. |
| 12 | Poor performance without a GPU (large mesh, shadows, high DPI). | 3 | 3 | 9 | Low-poly procedural geometry, no shadows, `devicePixelRatio` cap, frame-rate test. |
| 13 | Overall CAD output looks inconsistent with vessel outputs (Q9). | 3 | 3 | 9 | Cross-tab on day 1; documented explanation; derived "any vessel" indicator shown separately. |
| 14 | Judges expect "multimodal" beyond tabular data. | 3 | 3 | 9 | Modality-grouped explanations (Section 3.1) and clear wording in the Devpost text and video. |
| 15 | Explainer problems: SHAP slow or inconsistent with the deployed model (calibration wrapper, ensembles). | 3 | 3 | 9 | Choose the model family for explainability on day 2; precompute the explainer; cache; test that contributions sum to the prediction (additivity check). |
| 16 | Visual bugs undetectable in the sandbox (no browser): mirrored scene, mis-named nodes. | 3 | 3 | 9 | Headless unit tests for node names and mapping; human visual checklist (H10); screenshot proof in the doc. |
| 17 | Documentation exceeds 6 pages or lacks a required section. | 2 | 3 | 6 | Fixed outline (Section 7 day 9); page-count check in the acceptance test. |
| 18 | Dataset or mesh attribution/licence missing. | 2 | 3 | 6 | `CREDITS.md` and in-app credits; X-01, X-02 in acceptance tests. |
| 19 | Personal data or secrets pushed to a public repo (emails, keys, any real patient data). | 1 | 4 | 4 | `.gitignore`, secret scan before first push, real names only where required. |
| 20 | Live backend demo failure at judging time. | 2 | 2 | 4 | The video is the primary evidence; offer one-command local run plus an in-browser fallback if time permits. |

---

## 7. Acceptance-test checklist (one-to-one with the requirement IDs)

Each line is a binary check with the evidence to capture (screenshot, command output or link). "H" = needs a human.

### 7.1 Submission

| ID | Test | Evidence |
|---|---|---|
| SUB-01 | The Devpost project page shows description, repo link, video link and team, and its status reads Submitted. | H: screenshot |
| SUB-02 | Description has a "What it does/what we built" paragraph. | Page text |
| SUB-03 | Description has a "Problem" paragraph. | Page text |
| SUB-04 | Description has a "How it works" paragraph with an architecture diagram or list. | Page text |
| SUB-05 | The repo URL opens in an incognito window without sign-in. | H: incognito check |
| SUB-06 | `src`/code directories present, and code runs. | Repo listing |
| SUB-07 | `docs/` contains the PDF doc and README links to it. | Repo listing |
| SUB-08 | README has a "Setup" heading; a fresh clone succeeds following only that. | H: clean-machine run |
| SUB-09 | README has "Prerequisites" with exact versions (Python, Node, OS). | README text |
| SUB-10 | README has "Run" commands; app opens at the documented URL. | H: clean-machine run |
| SUB-11 | The video URL is a youtube.com or youtu.be link. | URL |
| SUB-12 | The video opens in incognito; its visibility setting says Unlisted or Public. | H: screenshot of YouTube Studio |
| SUB-13 | Duration shown by YouTube is between 3:00 and 10:00. | H: screenshot |
| SUB-14 | The video contains continuous footage of the running app, including recolouring of arteries. | Review pass |
| SUB-15 | The video has a segment (spoken) on dataset, model, explainability and 3D pipeline. | Script checklist |
| SUB-16 | English narration is audible, or English captions appear and are accurate. | H: listen/play with captions |
| SUB-17 | Every member's real full name appears on Devpost and matches the README credits. | H |
| SUB-18 | Each member can log in to Devpost. | H |
| SUB-19 | Each member shows on the public project page. | H: screenshot |
| SUB-20 | Team count is 4 or fewer. | Page |

### 7.2 Track A functional

| ID | Test | Evidence |
|---|---|---|
| TA-01 | `python train.py` produces a CAD model and a metrics row for the CAD target. | `metrics.json` |
| TA-02 | Same for LAD. | `metrics.json` |
| TA-03 | Same for LCX. | `metrics.json` |
| TA-04 | Same for RCA. | `metrics.json` |
| TA-05 | The feature schema file lists columns from each of the five groups and the model uses them. | Schema + model input list |
| TA-06 | Automated test: for each of the four targets, the feature list contains none of `LAD`, `LCX`, `RCA`, `Cath` (case-insensitive, also after one-hot encoding or renaming). | Test output |
| TA-07 | `metrics.json` and the dashboard show accuracy, precision, recall, F1 and ROC-AUC for all four targets (with CV spread). | File + screenshot |
| TA-08 | The app loads in a browser and shows a rotating 3D heart/torso built with an allowed library. | Screenshot, `package.json` |
| TA-09 | Changing an input slider changes vessel colours without reloading the page; colours match the displayed probabilities (test: probability 0.05, 0.5, 0.95 map to three different colours). | Unit test + screen capture |
| TA-10 | Mouse/touch drag rotates the model. | Video segment |
| TA-11 | Scroll/pinch zooms the model. | Video segment |
| TA-12 | Clicking each of LAD, LCX and RCA opens its detail panel (probability, top contributing features, caveat text). | Video segment |
| TA-13 | Overall CAD predicted status (label and probability) is visible on the same screen as the canvas. | Screenshot |
| TA-14 | All three vessel probabilities are visible on the same screen as the canvas. | Screenshot |
| TA-15 | A SHAP (or LIME) chart is shown for the current patient and for the selected target; additivity test (base value plus contributions equals output within tolerance). | Screenshot + test |
| TA-16 | Measured values (for example age, BP, LDL, EF-TTE) are listed with signed contribution and a modality grouping. | Screenshot |
| TA-17 | If a third-party mesh is used: its licence is in `CREDITS.md`; if procedural: stated in README. | File |
| TA-18 | A disclaimer banner is visible in the default viewport at 1366x768 without scrolling, and is not hideable permanently. | Screenshot |
| TA-19 | The banner or modal text includes "not a substitute for formal diagnostic imaging" (exact words or close paraphrase). | Text search in UI |

### 7.3 Deliverables

| ID | Test | Evidence |
|---|---|---|
| DEL-01 | The viewer's colours come from calls to the actual model (change the backend model file and see the output change; no hard-coded numbers). | Code review + test |
| DEL-02 | Linter passes; README maps modules; no dead notebooks; reproducible `make train`. | CI/terminal |
| DEL-03 | Weights file present in repo and loaded by the app; training regenerates it with the same metrics (seeded). | Hash/metrics |
| DEL-04 | A "Metrics" panel in the dashboard. | Screenshot |
| DEL-05 | A feature-importance (global) chart plus per-patient chart. | Screenshot |
| DEL-06 | A patient breakdown table/chart. | Screenshot |
| DEL-07 | `pdfinfo`/viewer: page count is 6 or fewer. | Command output |
| DEL-08 | Doc section "Dataset and preprocessing". | PDF |
| DEL-09 | Doc section "Model architecture". | PDF |
| DEL-10 | Doc section "3D pipeline". | PDF |
| DEL-11 | Doc section "Usage". | PDF |
| DEL-12 | Doc section "Evaluation results" with the table and plots. | PDF |
| DEL-13 | Video shows the working system. | Review pass |
| DEL-14 | Video shows entering or editing patient features. | Review pass |
| DEL-15 | Video shows rotate, zoom, select. | Review pass |
| DEL-16 | Video shows an architecture slide or code walkthrough. | Review pass |

### 7.4 Technical considerations and evaluation

| ID | Test | Evidence |
|---|---|---|
| TC-01 | On an integrated-graphics laptop (or Chrome with hardware acceleration disabled) the scene holds about 30 frames per second while rotating. | H: fps overlay screenshot |
| TC-02 | Add a dummy new feature to the schema/config and a new model entry; the UI form and prediction include them with no code edit outside config and data. | Demonstration commit |
| TC-03 | Test that node names are exactly `LAD`, `LCX`, `RCA`, that each is bound to the same-named model output, and that in the default view the RCA is on the viewer's left. | Unit test + screenshot |
| EV-1 | Metrics table with CV mean +/- SD, Brier, calibration curve, and the leakage test passing. | PDF + repo |
| EV-2 | Anatomically labelled vessels, uniform colouring, caption from Section 3.3, legend. | Screenshot |
| EV-3 | Local and global explanations, modality grouping, plain-language sentence per prediction. | Screenshot |
| EV-4 | Input change to visible recolour in under about 1 second; one command starts data, model and UI. | Screen recording |
| EV-5 | README, pinned versions, tests, dataset and mesh credits, licence file. | Repo check |
| X-01..X-08 | Credits file present; mesh credit present; pinned deps and seeded run; PDF in repo; limitations section; names in video credits; release tag; consistency note (Q9). | Repo/Devpost check |

---

## 8. Day-by-day schedule

Assumption: the deadline is about **2026-10-14** (Devpost showed "13 days to submit" on 2026-10-01). **The exact date, time and timezone are unconfirmed.** The Devpost Overview or Schedule tab must be read now (A-1). If the deadline is in the afternoon IST, or UTC-based, 10-14 loses its buffer; hence the plan submits on 10-13.

| Date | Day | Goals | Gate/exit criterion |
|---|---|---|---|
| 2026-10-04 | Sun | Team decisions (Section 3.2, Q1-Q9); confirm deadline/timezone and Rules (A-1..A-4); create the public repo (H3); download dataset (H1) and run the Section 4.4 checklist; assign roles (ML, 3D/front end, integration/docs, video/Devpost admin). | Deadline written on the team's board; dataset schema file exists |
| 2026-10-05 | Mon | Data pipeline with the single blacklist and the leakage test; baseline models on four targets with repeated CV; project skeleton (Vite + Three.js or R3F); procedural heart and three named vessels; API contract (JSON in/out); **every teammate has a Devpost account and is added to a draft project (H7)**. | Four baselines have metrics; scene renders; teammates on Devpost |
| 2026-10-06 | Tue | Model selection and calibration; export weights; SHAP pipeline and additivity test; mock-probability to colour mapping and rotate/zoom/select in the 3D scene. | Vertical slice: slider changes vessel colour (even with a stub) |
| 2026-10-07 | Wed | Backend integration (real model to viewer); patient input form for all features with ranges and units; dashboard layout (probabilities beside canvas); disclaimer banner and modal. | End-to-end flow works with the real model |
| 2026-10-08 | Thu | SHAP charts in UI; modality grouping; per-vessel detail panel; sample patient presets; node-name/mapping tests; performance pass on integrated graphics (H10). | TA-01..TA-19 each either passing or on a short fix list |
| 2026-10-09 | Fri | Draft documentation (6-page outline: preprocessing, model, 3D pipeline, usage, evaluation) and the README; fresh-clone test on a clean machine (H4); metrics finalised. | Docs draft; clean clone works |
| 2026-10-10 | Sat | **Feature freeze.** Polish, accessibility (colour-blind-safe scale, labels), caption text from Section 3.3, credits and licences; claims review; video script and storyboard. | Acceptance Sections 7.2 to 7.4 pass except video/Devpost |
| 2026-10-11 | Sun | Record the demo video (target 6-8 min); finalise the PDF doc (page count 6 or fewer). | Raw video recorded; PDF committed |
| 2026-10-12 | Mon | Edit video, add English captions, upload as Unlisted, check in incognito (H5, H6); complete the Devpost text, links and names; tag `v1.0-submission`. | SUB-11..16 pass |
| 2026-10-13 | Tue | Full dry run of the acceptance checklist (Section 7) by someone who did not write the code; **submit on Devpost** (target at least 24 hours before the deadline); screenshot the public project page. | Status Submitted; all SUB-xx pass |
| 2026-10-14 | Wed | Buffer and deadline day (about): only fix broken links, typos, a failed clone; do not change the model or UI. Re-verify that the repo is public and the video plays. | Final verification |

If the confirmed deadline is earlier than 10-14, compress by dropping the 10-08 polish items and the optional hosted demo, never the video, README or Devpost steps.

---

## 9. Items the team must decide (summary)

1. Interpretation of "overall cardiac risk" (Q1) and of "multi-vessel" output (Q2).
2. Mesh strategy: procedural (recommended) versus downloaded mesh with licence.
3. Calibration approach and model family (affects SHAP choice).
4. Inference location: local backend only, or also in-browser fallback.
5. Whether to include the dataset file in the repo (depends on the licence read in H1).
6. Whether to host a live demo (optional; no requirement found).
7. Confirmation of the deadline, Rules, and prize pool document.
