# ML-Assisted PACS System - Project Requirements
**Kalpa Inovasi Digital**  
**Document Date:** January 2026  
**First Customer:** Padma Medical Group

---

## 1. PROJECT OBJECTIVES

### 1.1 Business Goals
- Develop ML-assisted PACS as Kalpa product offering
- Target Indonesian clinic market (non-hospital)
- First deployment: Padma Medical Group (Bali, Surabaya)
- Revenue model: Subscription-based SaaS
- Cost target: <10,000 IDR per X-ray study

### 1.2 Clinical Problem Statement
**Current workflow gaps at Padma:**
- Senior technician triages normal vs abnormal X-rays
- Radiologist reviews flagged abnormals + bulk approves normals
- **Critical misses:** 3 abnormals misclassified as normal by tech (2 years), 1 abnormal dismissed by radiologist
- **Risk:** Delayed diagnosis, patient harm, liability exposure

**Solution:**
- ML model auto-flags suspicious findings
- Annotated overlay highlights abnormalities
- Mandatory radiologist review for ML-flagged studies
- Reduces dependency on tech triage accuracy

### 1.3 Technical Objectives
- DICOM-compliant PACS server
- Support non-Worklist equipment (majority of Indonesian clinics)
- ML inference pipeline for chest X-ray analysis
- WellMed integration (automatic study linking)
- Remote radiologist access
- Cloud-hosted (AWS)

---

## 2. SYSTEM ARCHITECTURE

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    CLINIC (Padma)                           │
│                                                             │
│  ┌──────────────┐                                          │
│  │  CR Reader   │ (Fujifilm IR-392)                        │
│  │  IR-392      │                                          │
│  └──────┬───────┘                                          │
│         │ DICOM C-STORE                                    │
│         │ (Direct to cloud via internet)                   │
└─────────┼─────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│              AWS CLOUD (Kalpa Infrastructure)               │
│                                                             │
│  ┌────────────────────────────────────────────┐            │
│  │          Orthanc PACS Server               │            │
│  │  - DICOM receiver (port 4242)              │            │
│  │  - Image storage (S3 backend)              │            │
│  │  - DICOMweb API                            │            │
│  │  - Webhook on new study                    │            │
│  └─────────────┬──────────────────────────────┘            │
│                │ HTTP POST (new study event)               │
│                ↓                                            │
│  ┌────────────────────────────────────────────┐            │
│  │      Kalpa Integration Service (Go)        │            │
│  │  - Receives Orthanc webhook                │            │
│  │  - Extracts RefID from DICOM tags          │            │
│  │  - Lookups order in WellMed                │            │
│  │  - Triggers ML pipeline                    │            │
│  │  - Updates WellMed study status            │            │
│  └─────────────┬──────────────────────────────┘            │
│                │ HTTP request                               │
│                ↓                                            │
│  ┌────────────────────────────────────────────┐            │
│  │      ML Inference Service (Python)         │            │
│  │  - Loads DICOM from Orthanc                │            │
│  │  - Runs inference (CheXNet/qXR)            │            │
│  │  - Generates findings JSON                 │            │
│  │  - Creates annotated overlay image         │            │
│  │  - Returns results                         │            │
│  └─────────────┬──────────────────────────────┘            │
│                │ Results JSON                               │
│                ↓                                            │
│  ┌────────────────────────────────────────────┐            │
│  │      Kalpa Integration Service (Go)        │            │
│  │  - Receives ML findings                    │            │
│  │  - Generates JPEG summary (annotated)      │            │
│  │  - Stores in WellMed patient record        │            │
│  │  - Creates FHIR ImagingStudy resource      │            │
│  │  - Flags for radiologist if needed         │            │
│  │  - Sends to SATU SEHAT                     │            │
│  └────────────────────────────────────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
          │
          ↓
┌─────────────────────────────────────────────────────────────┐
│                    WellMed HIS                              │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  Technician View                        │               │
│  │  - Pending orders with RefID            │               │
│  │  - JPEG preview of completed studies    │               │
│  │  - [Optional: Open DICOM viewer]        │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  Radiologist Review Queue               │               │
│  │  - ML-flagged studies (priority)        │               │
│  │  - Normal studies (bulk review)         │               │
│  │  - Click study → Opens OHIF in new tab  │               │
│  │  - ML findings pre-populated (grey)     │               │
│  │  - Edit/confirm/approve workflow        │               │
│  └─────────────────────────────────────────┘               │
│                                                             │
│  ┌─────────────────────────────────────────┐               │
│  │  GP/Doctor View                         │               │
│  │  - Patient encounter with studies       │               │
│  │  - JPEG summary with findings           │               │
│  │  - Radiologist report/impression        │               │
│  │  - [Optional: Open full DICOM]          │               │
│  └─────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Component Details

#### 2.2.1 Orthanc PACS Server
**Function:** DICOM storage and routing  
**Technology:** Orthanc 1.12+ (C++ core, Python plugins)  
**Deployment:** Docker container on AWS EC2  
**Storage:** AWS S3 (via Orthanc S3 plugin)  
**License:** AGPL (use as-is, proprietary services around it)

**Key capabilities:**
- DICOM receiver (C-STORE SCP)
- DICOMweb API (WADO-RS, QIDO-RS, STOW-RS)
- REST API for all operations
- Webhook on study received
- Modality Worklist provider (optional, future)

**Configuration:**
- Port 4242: DICOM protocol
- Port 8042: REST API + web interface
- Storage: S3 bucket with lifecycle policies
- Webhook: POST to Kalpa Go service on new study

#### 2.2.2 Kalpa Integration Service (Go)
**Function:** Business logic orchestration  
**Technology:** Go 1.21+, standard library + AWS SDK  
**Deployment:** ECS/Fargate or EC2 with auto-scaling

**Responsibilities:**
- Receive Orthanc webhooks
- Extract DICOM metadata (RefID, patient demographics)
- Query WellMed API for order matching
- Trigger ML inference
- Process ML results
- Generate JPEG summaries
- Update WellMed encounter/imaging study
- Create FHIR ImagingStudy resources
- Send to SATU SEHAT DICOM router

**Key endpoints:**
```
POST /api/dicom/received          # Orthanc webhook
UPDATE /api/dicom/update	      # Overwrite call
GET  /api/studies/{refId}         # Retrieve study by RefID
POST /api/studies/{id}/approve    # Radiologist approval
GET  /api/radiology/queue         # Pending review queue (orders)
```

#### 2.2.3 ML Inference Service (Python)
**Function:** Chest X-ray abnormality detection  
**Technology:** Python 3.11+, PyTorch/TensorFlow, FastAPI  
**Deployment:** EC2 with GPU (g4dn.xlarge or g5.xlarge)

**Responsibilities:**
- Load DICOM from Orthanc via DICOMweb
- Preprocess image (resize, normalize, CLAHE)
- Run inference with trained model
- Generate findings JSON (bounding boxes, confidence scores)
- Create annotated overlay image
- Return results to Integration Service

**Key endpoints:**
```
POST /api/ml/infer                # Run inference on study
GET  /api/ml/models               # List available models
GET  /api/ml/health               # Health check
```

**Model requirements:**
- Input: DICOM chest X-ray (PA view)
- Output: JSON with findings array
- Inference time: <10 seconds per study
- Confidence threshold: 0.70 for auto-flagging #configurable

---

## 3. TECHNOLOGY STACK

### 3.1 Core Components

| Component | Technology | Rationale |
|-----------|------------|-----------|
| **PACS Server** | Orthanc 1.12+ | Battle-tested DICOM protocol, Python plugins, REST API, active community |
| **Integration Service** | Go 1.21+ | Kalpa standard, performance, concurrency, AWS SDK support | #WellMed Gateway
| **ML Service** | Python 3.11+, PyTorch | ML ecosystem maturity, model availability, rapid iteration |
| **Web Viewer** | OHIF Viewer 3.x | Open-source, full-featured, DICOMweb native, React-based |
| **Storage** | AWS S3 | Cost-effective, durable, lifecycle management, Orthanc plugin available |
| **Database** | PostgreSQL 15+ | Orthanc index, WellMed orders, audit logs | #I think for MVP we run all (inference, service, db) on 1 server
| **Compute** | EC2 (dedicated), ECS (services) | Mix for cost optimization |

### 3.2 Why Not Alternatives?

**Why not dcm4chee?**
- Overkill for clinic market (enterprise complexity)
- Java stack (less familiar than Go/Python at Kalpa)
- Harder to customize/extend

**Why not custom Go DICOM server?**
- 6-12 months development time
- Maintaining DICOM protocol compliance is complex
- Orthanc proven, stable, actively maintained

**Why not cloud ML APIs (AWS Rekognition Medical)?**
- Cost: 3-5 USD/study vs 0.20 USD self-hosted
- Limited to AWS-approved findings (TB not included)
- No customization for Indonesian disease patterns

---

## 4. DICOM FUNDAMENTALS (Education)

### 4.1 DICOM Hierarchy

```
Patient
  └─ Study (single imaging session, e.g., chest X-ray today)
       └─ Series (logical grouping, e.g., PA view)
            └─ Instance (single image file, e.g., chest_pa.dcm)
```

**Example:**
- Patient: GUNAWAN SUSANTO (MRN: PMG001234)
- Study: Chest X-ray, 2026-01-29 10:30
  - Series 1: PA view (1 instance)
  - Series 2: Lateral view (1 instance)
  - Series 3: ML annotated overlay (1 instance)

### 4.2 Key DICOM Tags

| Tag | Name | Example | Usage |
|-----|------|---------|-------|
| (0010,0020) | Patient ID | PMG001234 | Patient matching |
| (0010,0010) | Patient Name | GUNAWAN^SUSANTO | Display |
| (0008,0020) | Study Date | 20260129 | Encounter matching |
| (0008,0050) | **Accession Number** | 290001 | **RefID (our key)** |
| (0008,0060) | Modality | CR, DX | Equipment type |
| (0020,000D) | Study Instance UID | 1.2.840... | Unique study ID |
| (0020,000E) | Series Instance UID | 1.2.840... | Unique series ID |

### 4.3 LOINC Codes for Imaging

**LOINC = Logical Observation Identifiers Names and Codes**

Used in FHIR ImagingStudy resources:

| Study Type | LOINC Code | Display |
|------------|------------|---------|
| Chest X-ray PA | 36643-5 | XR Chest PA |
| Chest X-ray 2 views | 30746-2 | XR Chest 2 views |
| Abdomen X-ray | 36680-7 | XR Abdomen |
| Lumbar spine AP/LAT | 37562-6 | XR Lumbar spine 2 views |

**Note:** LOINC codes map to ImagingStudy.procedureCode in FHIR, not required for DICOM itself.

---

## 5. INTEGRATION WORKFLOWS

### 5.1 Non-Worklist Integration (RefID-Based)

**This is the primary workflow for 95% of Indonesian clinics.**

#### 5.1.1 RefID Format

**Format:** `[PREFIX]DDNNNN`
- **PREFIX:** Modality identifier (1 character, optional/configurable)
  - X = X-ray
  - U = Ultrasound
  - E = EKG (future, non-DICOM)
  - A = Audiometry (future, non-DICOM)
  - S = Spirometry (future, non-DICOM)
  - T = Treadmill (future, non-DICOM)
- **DD:** Day of month (01-31)
- **NNNN:** Daily counter (0001-9999)

**Examples:**
- `X290001` = X-ray, Jan 29th, first study
- `U290015` = Ultrasound, Jan 29th, 15th study
- `290001` = No prefix (X-ray default if not configured)

**Collision avoidance:**
- Month boundaries: `010001` could be Feb 1 or Mar 1 (30 days apart, unmatched RefIDs don't collide)
- Prefix adds namespace separation per modality

**Generation logic:**
```go
// Pseudocode
func GenerateRefID(modalityType string, usePrefix bool) string {
    now := time.Now()
    day := now.Format("02") // 01-31
    
    // Get today's counter
    counter := db.Query("SELECT COUNT(*) FROM imaging_orders WHERE DATE(created_at) = CURDATE() AND modality = ?", modalityType)
    counter++
    
    refID := fmt.Sprintf("%s%04d", day, counter)
    
    if usePrefix {
        prefix := modalityPrefix[modalityType] // e.g., "X" for X-ray
        refID = prefix + refID
    }
    
    return refID
}
```

#### 5.1.2 Workflow Steps

**1. Doctor orders imaging in WellMed**
```
Doctor examines patient → Orders chest X-ray
WellMed creates:
  - Order record
  - RefID: 290001
  - Status: pending
```

**2. Technician performs study**
```
Tech logs into WellMed → "Pending Imaging Orders"
Sees: GUNAWAN SUSANTO - Chest PA - RefID: 290001
Clicks patient → RefID displayed prominently with [Copy] button
Tech copies RefID
Performs X-ray on patient
At FCRView console:
  - New Study
  - Accession Number field: Paste "290001"
  - Ready → Scan → Auto-send to PACS
```

**3. DICOM sent to Orthanc**
```
IR-392 → C-STORE to pacs.kalpa.cloud:4242
DICOM tags include:
  - Accession Number: "290001"
  - Patient ID: (blank or whatever tech entered)
  - Study Date: 20260129
Orthanc receives → Stores → Triggers webhook
```

**4. Kalpa Integration Service processes**
```go
// Webhook handler
func HandleDICOMReceived(studyInstanceUID string) {
    // Retrieve DICOM metadata from Orthanc
    dicom := orthanc.GetStudyMetadata(studyInstanceUID)
    refID := dicom.AccessionNumber // "290001"
    
    // Lookup order in WellMed
    order := wellmed.GetOrderByRefID(refID)
    if order == nil {
        quarantine.Add(studyInstanceUID, "Unknown RefID")
        return
    }
    
    // Update order status
    order.Status = "received"
    order.DICOMStudyUID = studyInstanceUID
    
    // Trigger ML pipeline
    mlService.QueueInference(studyInstanceUID, order.ID)
}
```

**5. ML inference runs**
```python
# ML service
def infer(study_uid):
    # Load DICOM from Orthanc
    dicom = orthanc_client.get_dicom(study_uid)
    image = preprocess(dicom.pixel_array)
    
    # Run model
    findings = model.predict(image)
    # findings = [
    #   {"type": "infiltrate", "confidence": 0.82, "bbox": [...]},
    #   {"type": "cardiomegaly", "confidence": 0.68, "bbox": [...]}
    # ]
    
    # Generate annotated overlay
    overlay = create_overlay(image, findings)
    
    return {
        "findings": findings,
        "overlay_png": overlay_base64
    }
```

**6. Results processed**
```go
func ProcessMLResults(studyUID string, results MLResults) {
    order := getOrderByStudyUID(studyUID)
    
    // Store findings in order
    order.MLFindings = results.Findings
    
    // Generate JPEG summary
    jpeg := generateJPEGSummary(results.OverlayPNG)
    s3.Upload(jpeg, fmt.Sprintf("studies/%s/summary.jpg", order.ID))
    
    // Create FHIR ImagingStudy
    imagingStudy := createImagingStudy(order, studyUID)
    
    // Flag for radiologist if high-confidence findings
    if hasHighConfidenceFindings(results.Findings, 0.70) {
        order.Status = "flagged_for_radiologist"
        notify.Radiologist(order)
    } else {
        order.Status = "completed_normal"
    }
    
    // Update WellMed
    wellmed.UpdateOrder(order)
    
    // Send to SATU SEHAT
    satuSehat.SendImagingStudy(imagingStudy)
}
```

**7. Radiologist reviews**
```
Radiologist logs into WellMed → "Radiology Review Queue"
Sees flagged studies (ML high-confidence) at top
Clicks study → Opens in new tab:
  - OHIF viewer with full DICOM
  - ML findings pre-populated in notes (grey text, editable)
  
Radiologist:
  - Views images in OHIF (window/level adjust, zoom, etc.)
  - Returns to WellMed tab
  - Edits ML findings (confirm/modify/delete)
  - Adds impression using template snippets
  - Clicks [Approve]
  
Order status → "radiologist_approved"
Doctor notified → Report visible in encounter
```

#### 5.1.3 Error Handling

**Scenario: Tech typos RefID**
```
Tech enters: 290012 (should be 290001)
Integration Service: Order not found
Action: Quarantine study
UI: Staff sees quarantine queue
  - "Unknown RefID: 290012"
  - Search shows: "Did you mean 290001?"
  - Click to link → Resolved
```

**Scenario: Tech forgets to enter RefID**
```
Accession Number: (blank)
Integration Service: No RefID
Fallback: Try Patient ID matching (if tech entered)
If still no match: Quarantine
```

**Scenario: Multiple studies same RefID (legitimate repeat)**
```
Tech does Chest PA → RefID: 290001
Tech does Chest Lateral → RefID: 290001 (same order)
Integration Service: 
  - Sees duplicate RefID
  - Checks: Same patient, same day, reasonable time gap
  - Action: Append as additional series to same ImagingStudy
```

### 5.2 Worklist Integration (Future Enhancement)

**For clinics that purchase DICOM Worklist license (~30M IDR)**

#### 5.2.1 Architecture Addition

```
WellMed (FHIR ServiceRequest)
  ↓
Kalpa FHIR → DICOM Worklist Bridge (Go)
  ↓ MWL C-FIND SCP
Modality queries worklist
  ↓
Modality pre-populates patient data
  ↓
Study sent with all metadata correct
```

#### 5.2.2 Workflow Improvement

**Without Worklist (current):**
- Tech enters RefID manually: 10 seconds
- Error rate: 0.1-0.3%

**With Worklist:**
- Tech sees patient list at modality console
- Selects patient: 3 seconds
- Error rate: <0.05%

**ROI calculation:**
- Time saved: 7 sec/study × 1200 studies/year = 2.3 hours/year
- At 100k/hour = 230k/year savings
- Worklist license: 30M IDR
- Payback: 130 years (not worth it at current volume)

**When Worklist makes sense:**
- Volume >40 studies/day (10,000+/year)
- Or error rate critical (surgical centers)

**Implementation priority:** Phase 3 (2027+)

---

## 6. ML MODEL EVALUATION

### 6.1 Clinical Requirements

**Target conditions (Padma priority):**
1. **Tuberculosis** (infiltrates, cavitation, pleural effusion)
2. **Cardiomegaly** (enlarged heart, cardiothoracic ratio >0.5)
3. **Scoliosis** (spine curvature)
4. **Pneumonia** (consolidation, infiltrates)
5. **Pleural effusion** (fluid in lungs)

**Lower priority:**
- Pneumothorax (rare in MCU population)
- Nodules/masses (detected but not prioritized)
- Fractures (visible on X-ray review anyway)

### 6.2 Model Options

| Model | Findings Coverage | TB Detection | Scoliosis | Strengths | Limitations |
|-------|-------------------|--------------|-----------|-----------|-------------|
| **CheXNet (Stanford)** | 14 pathologies | Good (infiltrates) | No | Research-validated, free, well-documented | No scoliosis, older (2017) |
| **qXR (Qure.ai)** | 29 findings | Excellent | Yes | Most comprehensive, TB-specific, active learning | Commercial (free tier limited) |
| **Lunit INSIGHT CXR** | 10 key findings | Good | No | Fast, accurate, production-ready | Limited finding types |
| **PadChest (Spain)** | 174 labels | Excellent | Yes | Massive label set, research dataset | Heavy model, slow inference |
| **VinDr-CXR (Vietnam)** | 28 findings | Excellent | Partial | Asian population trained, open-source | Less documentation |

### 6.3 Recommended Approach

**Phase 1 (Q3-Q4 2026): Single model baseline**

**Primary model: qXR (Qure.ai)**
- **Rationale:**
  - Best TB detection (critical for Indonesia)
  - Includes scoliosis (Padma priority)
  - 29 findings = comprehensive
  - Production-ready (used in India, similar market)
  - Free tier: 1000 studies/month (sufficient for pilot)
- **License:** Commercial after free tier
  - Cost: 10-15 USD/study (~150k IDR) if using API
  - Alternative: On-premise deployment (negotiable pricing)

**Backup model: CheXNet**
- Free, open-source
- Acceptable accuracy (90-95% on 14 pathologies)
- Use if qXR commercial terms unfavorable

**Phase 2 (2027): Ensemble approach**
- Add specialist models:
  - TB-specific: VinDr-CXR or PadChest
  - Scoliosis-specific: Custom-trained on local data
- Combine outputs: Voting or weighted average
- Improves sensitivity (catch more abnormals)

### 6.4 Performance Metrics

**Target performance (vs senior tech triage):**
- Sensitivity: >95% (catch abnormals)
- Specificity: 80-85% (avoid false alarms)
- NPV (Negative Predictive Value): >99% (if ML says normal, trust it)

**Acceptable trade-off:**
- Over-flagging acceptable (radiologist reviews anyway)
- Under-flagging unacceptable (misses are critical)

**Confidence threshold tuning:**
- Start: 0.70 (conservative, more flags)
- Adjust based on radiologist feedback
- Goal: 20-30% flagged (vs 100% manual review)

### 6.5 Model Deployment

**Infrastructure:**
- GPU: NVIDIA T4 (g4dn.xlarge) or A10G (g5.xlarge)
- RAM: 16GB minimum
- Storage: 50GB for model + cache
- Inference time: 5-10 seconds per study

**Optimization:**
- Model quantization (FP16 or INT8) for speed
- Batch processing for bulk uploads
- GPU sharing for multiple models (future)

**Monitoring:**
- Log all predictions (for retraining)
- Track confidence distribution
- Alert on model degradation
- A/B test model updates

---

## 7. MODALITY CONNECTIVITY

### 7.1 Supported Equipment Types

**DICOM modalities (direct connection):**
- **CR (Computed Radiography):** Fujifilm IR-392, Agfa CR30
- **DR (Digital Radiography):** Mindray DigiEye, Fujifilm FDR, GE Revolution
- **Ultrasound:** Mindray DP-30, DC-70, SonoScape S40
- **CT:** (future, hospital-tier)
- **MRI:** (future, hospital-tier)

**Configuration requirements:**
- Static IP or dynamic DNS for cloud PACS
- Internet connectivity (minimum 1 Mbps upload)
- DICOM destination config: `pacs.kalpa.cloud:4242`
- AE Title: `KALPA_PACS`

### 7.2 Connection Methods

**Method A: Direct push (recommended for clinics with stable internet)**
```
Modality → Internet → Cloud Orthanc (pacs.kalpa.cloud:4242)
```
- Pros: No local hardware, simple setup
- Cons: Requires internet during scan (usually fine)

**Method B: Local buffering (for unreliable internet)**
```
Modality → Local Orthanc (Raspberry Pi/NUC) → Periodic sync → Cloud
```
- Pros: Works offline, buffers locally
- Cons: Hardware at clinic, more complex

**Padma pilot: Method A (direct push)**

**Kalpa product: Offer both, Method A default**

### 7.3 Network Requirements

**Bandwidth:**
- CR study: ~8-15 MB (uncompressed)
- Upload time at 1 Mbps: ~90 seconds
- Upload time at 10 Mbps: ~9 seconds
- Recommended: 5+ Mbps upload

**Latency tolerance:**
- DICOM protocol: Tolerates 500ms+ latency
- Not real-time critical

**Firewall:**
- Outbound TCP port 4242: Allow
- Inbound: None needed (modality pushes)

**VPN/Security:**
- TLS encryption: Available in Orthanc (DICOM-TLS)
- VPN: Optional (adds complexity, not required for DICOM-TLS)
- Recommend: DICOM-TLS for production

### 7.4 Disaster Recovery

**Local logging (no gateway hardware):**
```
Modality → Sends to cloud
         → Also saves to local storage (if supported)
```

**Most modern CR/DR systems support:**
- Internal buffer: 50-200 studies
- Retry on network failure
- Manual re-send if needed

**Kalpa responsibility:**
- Cloud PACS uptime: 99.5%+
- Redundant storage (S3 multi-region)
- Daily backups (S3 glacier)

**Clinic responsibility:**
- Internet uptime (use backup LTE if critical)
- Monitor send failures on modality console

---

## 8. INFRASTRUCTURE REQUIREMENTS

### 8.1 AWS Components

| Component | Service | Spec | Monthly Cost (USD) |
|-----------|---------|------|-------------------|
| **PACS Server** | EC2 t3.large | 2 vCPU, 8GB RAM | 60 |
| **ML Server** | EC2 g4dn.xlarge (spot) | 4 vCPU, 16GB RAM, T4 GPU | 80 |
| **Integration Service** | ECS Fargate | 2 vCPU, 4GB RAM × 2 tasks | 60 |
| **Database** | RDS PostgreSQL db.t3.medium | 2 vCPU, 4GB RAM | 70 |
| **Storage** | S3 Standard + Glacier | 500GB/month + 5TB archive | 30 |
| **Data Transfer** | Outbound | ~500GB/month (JPEG serving) | 45 |
| **Load Balancer** | ALB | 2 targets | 25 |
| **Total** | | | **~370 USD/month** |

**Scaling assumptions:**
- 50 studies/day average (1500/month)
- 10 MB per study = 15 GB/month new
- 5-year archive = 900 GB cumulative
- JPEG serve: 500 KB × 1500 × 20 views = 15 GB/month

**Cost per study: ~0.25 USD (~3,900 IDR)**

**At target 10k IDR/study:**
- Infrastructure: 3,900 IDR (39%)
- ML compute: Included in above
- Remaining: 6,100 IDR (61%) for margin/operations

### 8.2 Scaling Model

**Tier 1: Single clinic (baseline above)**
- 50 studies/day
- 370 USD/month
- Cost/study: 0.25 USD

**Tier 2: 5 clinics**
- 250 studies/day
- Add: 1× g4dn (dedicated), storage +200 GB
- 620 USD/month
- Cost/study: 0.16 USD (economies of scale)

**Tier 3: 20 clinics**
- 1000 studies/day
- Add: 2× g4dn, storage +1 TB, RDS scale up
- 1,400 USD/month
- Cost/study: 0.09 USD (further economies)

**ML compute optimization:**
- Spot instances: 70% cost savings
- Reserved instances (1-year): 30% savings after proof-of-concept
- GPU sharing: Multiple models on single instance

### 8.3 Development Environment

**Staging environment:**
- Scaled-down replica of production
- Cost: ~150 USD/month
- Use for testing, demos, training

**Local development:**
- Docker compose: Orthanc + PostgreSQL + mock ML
- Developers run locally
- No cloud cost for development

---

## 9. MARKET ANALYSIS

### 9.1 Indonesian Clinic Market

**Market size:**
- Primary healthcare facilities: ~10,000 (Puskesmas + private clinics)
- Clinics with X-ray: ~3,000
- Target: Private clinics (500 facilities)

**Current PACS penetration:**
- Hospital market: 60-70% (mostly international vendors)
- Clinic market: <10% (mostly paper/film or local drives)
- Opportunity: 2,700+ clinics without PACS

**Buying behavior:**
- Decision maker: Clinic owner/director
- Budget authority: 50-200M IDR/year IT spend
- Purchase cycle: 3-6 months (demo → approval → implementation)
- Payment: Monthly subscription preferred over upfront

### 9.2 Competitor Landscape

**International vendors (hospital-focused):**

| Vendor | Product | Target | Price (IDR/month) | Strengths | Weaknesses |
|--------|---------|--------|-------------------|-----------|------------|
| **GE Healthcare** | Centricity PACS | Hospital | 100-300M/year | Brand, integration | Expensive, overkill for clinics |
| **Philips** | IntelliSpace | Hospital | 150-400M/year | Full ecosystem | Enterprise complexity |
| **Fujifilm** | Synapse PACS | Hospital/large clinic | 50-150M/year | Modality integration | Not cloud-native |

**Local/regional vendors (clinic-focused):**

| Vendor | Product | Target | Price (IDR/month) | Strengths | Weaknesses |
|--------|---------|--------|-------------------|-----------|------------|
| **Neusoft (China)** | NeuViz PACS | Mid-size clinic | 10-30M | Affordable | No ML, limited support |
| **Medico (Indo)** | MediVision | Small clinic | 5-15M | Local support | Basic features, no ML |
| **Visiana (Indo)** | VisianaPACS | Clinic/imaging center | 8-20M | Indonesia-focused | Limited scalability |

**Cloud PACS (emerging):**
- **Ambra Health** (US): 15-40M/month, no Indonesia presence
- **Nuance PowerShare** (US): 20-50M/month, hospital-tier

### 9.3 Competitive Positioning

**Kalpa ML-PACS differentiators:**

1. **ML-assisted reading** (unique in Indonesia clinic market)
   - Competitors: None have ML at clinic price point
   - Value: Catch misses, reduce liability

2. **WellMed integration** (proprietary advantage)
   - Seamless ordering → imaging → reporting
   - RefID-based workflow (no expensive Worklist licenses)

3. **Cloud-native architecture** (vs on-premise legacy)
   - No hardware at clinic
   - Automatic updates
   - Remote radiologist access built-in

4. **Indonesia-specific** (vs international generic)
   - SATU SEHAT integration
   - Indonesian language
   - Local support/training
   - TB-focused ML models

5. **Pricing** (affordable for clinics)
   - Target: 10-25M IDR/month (vs 50-150M competitors)
   - Subscription (vs 200-500M upfront)

---

## 10. PRICING MODELS

### 10.1 Cost Analysis

**Base infrastructure cost per clinic:**
- Marginal cost at scale (20+ clinics): ~0.09 USD/study
- At 1500 studies/month: 135 USD = 2.1M IDR


### 10.2 Pricing (Conceptual)

**Option A: Flat monthly subscription (recommended)**
```
Price: 6M IDR/month
Includes:
  - Studies (fair use: 1000/month)
  - ML analysis on all chest X-rays
  - WellMed integration
  - Remote radiologist access
  - SATU SEHAT reporting
  - Support (email, 24-hour response)

Overage: 10,000 IDR/study beyond 1000/month
```


Price: 20,000 IDR/study
Minimum: 4M IDR/month (covers ~200 studies)

Includes:
  - ML analysis
  - Storage (5-year retention)
  - All features
```


### 10.3 Recommended Pricing Strategy

**Launch pricing (first 12 months):**
- **4M IDR/month** (50% discount)
- Includes all features

**Target pricing (steady state):**
- **8M IDR/month**
- Monthly or annual (annual 10% discount)

**Add-ons (future):**
- DICOM Worklist integration: +3M IDR/month
- Package (enterprise) up to 3000 studies per month for 15 JT includes worklist piece
- Additional modalities (ultrasound, CT): +5M IDR/month each	
- Advanced reporting module: +2M IDR/month
- Teleradiology marketplace: Commission-based (20% of rad fee)

**Competitive comparison:**
- Local PACS (no ML): 8-15M IDR/month → **Kalpa: 15M (premium for ML)**
- International PACS: 50-150M IDR/month → **Kalpa: 5-10× cheaper**
- Paper/film cost: ~10k IDR/study × 1500 = 15M/month → **Kalpa: Same cost, digital + ML**

**Value proposition:**
- Efficiency: Save 30 min/day × 300 days = 150 hours/year = 15M IDR labor
- Marketing: "AI-assisted radiology" = attract more patients

### 10.4 Revenue Projections

**Year 1 (2026):**
- Customers: 5 clinics (Padma + 4 new)
- ARPU: 12M IDR/month (launch pricing)
- MRR: 60M IDR
- ARR: 720M IDR

**Year 2 (2027):**
- Customers: 20 clinics
- ARPU: 14M IDR/month (mix of launch + standard)
- MRR: 280M IDR
- ARR: 3.36B IDR

**Year 3 (2028):**
- Customers: 50 clinics
- ARPU: 15M IDR/month (standard pricing)
- MRR: 750M IDR
- ARR: 9B IDR

**Assumptions:**
- Churn: 10% annually (clinics close, switch)
- CAC (Customer Acquisition Cost): 30M IDR (2 months ARPU)
- Payback: 6 months
- LTV/CAC ratio: 6× (healthy SaaS metric)

---

## 11. GO-TO-MARKET CONSIDERATIONS

### 11.1 Sales Strategy

**Target customer profile:**
- Private clinic with X-ray equipment
- 20-50 patients/day
- Annual revenue: 2-10B IDR
- Current: Paper/film or basic local storage
- Pain: Radiologist access, compliance, quality concerns

**Sales channels:**
1. **Direct sales** (first 20 customers)
   - Founder-led (Alex Knecht)
   - Focus: Jakarta, Surabaya, Bali
   - Method: Personal network, referrals

2. **Equipment dealer partnerships** (scale)
   - Partner with Mindray, Fujifilm dealers
   - Bundle: Buy DR/CR + 1-year Kalpa PACS
   - Commission: 10-20% of year-1 revenue

3. **Medical association** (credibility)
   - Present at PAPDI (Indonesian Physicians Association)
   - Case study: Padma's ML catch rate
   - Word-of-mouth

**Sales cycle:**
- Initial contact → Demo (1 week)
- Demo → Trial (2-4 weeks)
- Trial → Contract (2-4 weeks)
- Total: 1-3 months

**Trial program:**
- Free 30-day trial
- Full features (ML, WellMed integration)
- Setup included
- Convert: 60-70% (industry benchmark)

### 11.2 Implementation

**Onboarding process:**
1. **Equipment configuration** (Day 1, 2 hours)
   - Configure DICOM destination on modality
   - Test send (phantom study)
   - Verify receipt in Orthanc

2. **WellMed integration** (Day 2-3, 4 hours)
   - Configure RefID generation
   - Set up technician pending orders view
   - Train radiologist on review queue

3. **Training** (Day 3, 3 hours)
   - Technician: How to use RefID workflow
   - Radiologist: OHIF viewer, ML findings, approval
   - Admin: Quarantine queue, troubleshooting

4. **Go-live** (Day 4)
   - First real patient study
   - Monitor closely
   - On-site support available

**Total implementation: 1 week**

**Support model:**
- Email: support@kalpa.id (24-hour response)
- WhatsApp: For urgent issues
- Remote access: TeamViewer/AnyDesk for troubleshooting
- On-site: As needed (billable after first month)

### 11.3 Regulatory Compliance

**Indonesia requirements:**
- **Medical device registration:** PACS is not a medical device (software only, no diagnosis)
- **Data privacy:** Comply with UU PDP (Indonesia data protection law)
  - Patient consent for data storage
  - Encryption at rest/transit
  - Audit logs (who accessed what)
- **SATU SEHAT:** Integration required for government facilities (private optional but recommended)
- **Radiology licensing:** Radiologist must be registered (not our responsibility, clinic's)

**Data residency:**
- Host in AWS Singapore (ap-southeast-1)
- Indonesia region (Jakarta) when available
- No data leaves APAC region

**Compliance strategy:**
- Privacy policy template for clinics
- Data Processing Agreement (DPA) in contract
- Annual security audit (ISO 27001 path for future)

---

## 12. SUCCESS METRICS

### 12.1 Technical Metrics

**System performance:**
- PACS uptime: >99.5%
- DICOM receive latency: <5 seconds
- ML inference time: <10 seconds
- JPEG generation: <30 seconds total
- End-to-end (scan → viewable): <60 seconds

**ML performance:**
- Sensitivity (catch abnormals): >95%
- Specificity: >80%
- False positive rate: <20%
- Radiologist agreement: >90%

**Integration success:**
- RefID match rate: >99%
- Quarantine rate: <1%
- SATU SEHAT send success: >98%

### 12.2 Business Metrics

**Customer metrics:**
- Clinics onboarded: 5 (Year 1), 20 (Year 2)
- Churn rate: <10% annually
- NPS (Net Promoter Score): >50
- Trial → paid conversion: >60%

**Usage metrics:**
- Studies/month/clinic: 1200-1800 (active usage)
- ML flag rate: 20-30% (tuned to avoid over-flagging)
- Radiologist review time: <2 min/study (acceptable)

**Revenue metrics:**
- MRR growth: 20% month-over-month (first year)
- CAC payback: <6 months
- LTV/CAC: >6×
- Gross margin: >60% (after scaling)

### 12.3 Clinical Impact Metrics

**Safety metrics (most important):**
- Missed abnormals (ML + radiologist): 0 (goal)
- ML-caught cases (that tech/radiologist would have missed): Track quarterly
- False reassurance (ML says normal, actually abnormal): <1% (critical threshold)

**Quality metrics:**
- Radiologist satisfaction: Survey quarterly
- Referring doctor satisfaction: Report turnaround time, quality
- Patient outcomes: Track (requires long-term study)

**Compliance:**
- SATU SEHAT submission rate: 100% (government facilities)
- Audit trail completeness: 100%
- Data breach incidents: 0

---

## 13. RISKS & MITIGATION

### 13.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ML model underperforms (misses abnormals) | High | Medium | Extensive validation on Indonesian data, conservative thresholds, human-in-loop |
| Orthanc scalability issues | Medium | Low | Load testing, horizontal scaling plan, fallback to dcm4chee |
| DICOM protocol compatibility issues | Medium | Medium | Test with all major modality vendors, maintain compatibility matrix |
| AWS outage | Medium | Low | Multi-AZ deployment, automated failover, 4-hour RTO target |
| Data loss | High | Very Low | S3 versioning, cross-region replication, daily backups |

### 13.2 Business Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Low customer adoption | High | Medium | Free trial, flexible pricing, strong Padma case study |
| Competitor launches similar product | Medium | Medium | Speed to market (first-mover), proprietary WellMed integration |
| Pricing too high for market | Medium | Medium | Market research, flexible pricing tiers, value-based selling |
| Regulatory changes require major changes | Medium | Low | Monitor regulatory landscape, modular architecture allows adaptation |

### 13.3 Clinical/Legal Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| ML misses critical finding → Patient harm | Very High | Low | Conservative ML thresholds, radiologist always reviews, clear liability in T&Cs |
| Radiologist over-relies on ML → Complacency | High | Medium | Training emphasizes ML is assistant not replacement, audit flag/approval correlation |
| Data breach → Patient privacy violation | High | Low | Encryption, access controls, regular security audits, cyber insurance |
| Liability dispute (who's responsible for miss?) | High | Low | Clear contract terms: Radiologist has final authority, ML is decision support tool |

**Liability strategy:**
- Kalpa provides decision support tool (not diagnostic device)
- Final diagnosis/report is radiologist's responsibility
- Insurance: Professional indemnity for software providers
- Contract: Indemnification clause for proper use

---

## 14. DEVELOPMENT ROADMAP

### 14.1 Phase 1: MVP (Q3 2026, 3 months)

**Scope:**
- Orthanc PACS deployment (AWS)
- Basic Kalpa Integration Service (Go)
- Single ML model (qXR or CheXNet)
- RefID-based workflow
- WellMed integration (basic)
- OHIF viewer (off-the-shelf)
- Padma pilot (Surabaya IR-392)

**Team:**
- 1× Backend engineer (Go)
- 1× ML engineer (Python)
- 1× DevOps engineer (AWS, Orthanc)
- 0.5× Product (Alex)

**Deliverables:**
- Working PACS receiving DICOM from IR-392
- ML running on all chest X-rays
- Findings visible in WellMed
- Radiologist can review/approve

### 14.2 Phase 2: Production (Q4 2026, 2 months)

**Scope:**
- Production hardening (monitoring, alerts, logging)
- Quarantine queue UI
- Radiologist review queue improvements
- SATU SEHAT integration
- Security audit + penetration testing
- Multi-clinic support
- Onboard 3-4 additional clinics

**Team:**
- Same as Phase 1 + 0.5× Frontend (WellMed UI)

**Deliverables:**
- Production-ready system (99%+ uptime)
- 5 clinics live
- SATU SEHAT submissions working
- Support processes established

### 14.3 Phase 3: Scale (2027, ongoing)

**Scope:**
- Multiple ML models (ensemble)
- DICOM Worklist support (optional add-on)
- Ultrasound support
- Advanced reporting templates
- Teleradiology marketplace
- Mobile app for radiologists
- Expand to 20+ clinics

**Team:**
- Add: 1× Sales, 1× Customer success

**Deliverables:**
- 20+ clinics
- MRR: 250M+ IDR
- Product-market fit validated

---

## 15. APPENDICES

### 15.1 Glossary

**DICOM:** Digital Imaging and Communications in Medicine - Standard protocol for medical imaging  
**PACS:** Picture Archiving and Communication System - Medical image storage/viewing system  
**CR:** Computed Radiography - Uses imaging plates (older technology)  
**DR:** Digital Radiography - Direct digital capture (newer)  
**Worklist:** DICOM MWM - Modality worklist management (pre-populates patient data)  
**RefID:** Reference identifier - Kalpa's order tracking code  
**ML:** Machine Learning - AI models for image analysis  
**OHIF:** Open Health Imaging Foundation - Open-source DICOM viewer  
**Orthanc:** Open-source DICOM server  
**FHIR:** Fast Healthcare Interoperability Resources - Modern health data standard  
**ImagingStudy:** FHIR resource representing imaging exam  
**SATU SEHAT:** Indonesia national health data platform  

### 15.2 Reference Architecture Diagram

See Section 2.1 for detailed architecture diagram.

### 15.3 Sample RefID Workflow

```
Time: 09:00 - Doctor orders chest X-ray
  WellMed → Order created
  RefID: 290045
  Status: pending

Time: 09:15 - Tech performs X-ray
  Tech opens WellMed → Sees "GUNAWAN SUSANTO - Chest PA - RefID: 290045"
  Copies RefID
  At FCRView: Accession Number = "290045"
  Scan complete → DICOM sent

Time: 09:16 - PACS receives
  Orthanc → Stores DICOM
  Webhook → Kalpa Integration Service
  Lookup order by RefID 290045 → Found
  Trigger ML pipeline

Time: 09:17 - ML inference
  ML Service → Processes image
  Findings: Infiltrate (confidence 0.82), Cardiomegaly (0.68)
  Generate overlay
  Return results

Time: 09:18 - Results processed
  Integration Service → Receives findings
  Create JPEG summary
  Update WellMed order: Status = "flagged_for_radiologist"
  Send to SATU SEHAT

Time: 14:30 - Radiologist reviews
  Radiologist logs in → Review queue
  Sees GUNAWAN study (flagged)
  Clicks → OHIF opens in new tab
  Reviews findings (confirms infiltrate, notes cardiomegaly)
  Returns to WellMed → Edits impression
  Clicks "Approve"

Time: 14:31 - Complete
  Order status: "radiologist_approved"
  Doctor notified
  Report visible in encounter
```

### 15.4 Contact Information

**Project Owner:** Alex Knecht (Director of Growth, Padma Medical Group)  
**Development Team:** Kalpa Inovasi Digital  
**Pilot Site:** Padma Medical Group Surabaya  
**Timeline:** Q3 2026 start

---

**Document Version:** 1.0  
**Last Updated:** January 29, 2026  
**Next Review:** July 2026 (post-MVP)
