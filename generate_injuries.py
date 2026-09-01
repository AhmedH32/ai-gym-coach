import os
from pathlib import Path

OUTPUT_DIR = Path("rag_corpus/injuries")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONDITIONS = [
    # --- SHOULDER (7) ---
    {
        "file": "subacromial_impingement.md",
        "id": "COND_SUBACROMIAL_IMPINGEMENT",
        "name": "Subacromial Impingement Syndrome",
        "category": "Shoulder",
        "mechanism": "Compression and mechanical attrition of the supraspinatus tendon, long head of biceps tendon, and subacromial bursa within the subacromial space during shoulder abduction and internal rotation.",
        "contraindications": [
            "Overhead pressing with internal rotation (e.g., Behind-the-neck press)",
            "Upright rows above chest height",
            "Dips extending into extreme shoulder extension",
            "Empty can exercise (abduction in internal rotation)"
        ],
        "modifications": [
            "Limit shoulder abduction to below 90 degrees or press in the scapular plane (30-45 degrees anterior to coronal plane)",
            "Maintain external rotation during pressing movements (e.g., neutral grip / palms facing each other)",
            "Avoid full end-range internal rotation during loaded overhead movements"
        ],
        "substitutions": [
            "Landmine overhead press instead of standing barbell overhead press",
            "Neutral-grip dumbbell shoulder press instead of wide-grip barbell shoulder press",
            "High-to-low cable face pulls emphasizing external rotation"
        ],
        "sources": [
            ("Physiopedia - Subacromial Impingement Syndrome", "https://www.physio-pedia.com/Subacromial_Impingement_Syndrome"),
            ("NCBI StatPearls - Subacromial Impingement Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK538164/")
        ]
    },
    {
        "file": "ac_joint_sprain.md",
        "id": "COND_AC_JOINT_SPRAIN",
        "name": "Acromioclavicular (AC) Joint Sprain",
        "category": "Shoulder",
        "mechanism": "Direct impact or high horizontal adduction forces causing tearing or sprain of the acromioclavicular and coracoclavicular ligaments, leading to localized joint destabilization.",
        "contraindications": [
            "Cross-body horizontal adduction under load (e.g., pec deck or cable crossovers across midline)",
            "Deep barbell bench press extending elbows far behind the torso",
            "Dips with heavy axial loading"
        ],
        "modifications": [
            "Limit elbow extension behind the torso on bench press (use floor press or board press)",
            "Maintain a narrower grip width (shoulder-width or neutral) to reduce AC joint compression",
            "Avoid cross-body arm position at end-range horizontal adduction"
        ],
        "substitutions": [
            "Neutral-grip dumbbell floor press instead of deep wide-grip barbell bench press",
            "Neutral-grip chest-supported dumbbell row instead of wide-grip upright row",
            "Push-ups with hands elevated on handles/blocks restricting deep shoulder extension"
        ],
        "sources": [
            ("Physiopedia - Acromioclavicular Joint Injury", "https://www.physio-pedia.com/Acromioclavicular_Joint_Injury"),
            ("NCBI StatPearls - Acromioclavicular Joint Injury", "https://www.ncbi.nlm.nih.gov/books/NBK537189/")
        ]
    },
    {
        "file": "rotator_cuff_tendinopathy.md",
        "id": "COND_ROTATOR_CUFF_TENDINOPATHY",
        "name": "Rotator Cuff Tendinopathy",
        "category": "Shoulder",
        "mechanism": "Repetitive tensile overload or compressive impingement causing micro-tears, collagen disorganization, and localized vascular compromise in the rotator cuff tendons (supraspinatus, infraspinatus, subscapularis, teres minor).",
        "contraindications": [
            "Heavy explosive overhead lifting (e.g., snatch, push jerk)",
            "Behind-the-neck lat pulldowns or shoulder presses",
            "Extreme end-range shoulder extension combined with internal rotation"
        ],
        "modifications": [
            "Perform shoulder exercises strictly in the scapular plane with sub-maximal loads",
            "Control eccentric tempo and eliminate rapid direction changes under load",
            "Keep grip neutral to minimize compressive forces on the supraspinatus insertion"
        ],
        "substitutions": [
            "Scaption dumbbell raises (elevation in scapular plane) instead of lateral raises in pure frontal plane",
            "Incline dumbbell bench press with neutral grip instead of flat barbell bench press",
            "Cable side-lying external rotations for targeted cuff capacity"
        ],
        "sources": [
            ("Physiopedia - Rotator Cuff Tendinopathy", "https://www.physio-pedia.com/Rotator_Cuff_Tendinopathy"),
            ("NCBI StatPearls - Rotator Cuff Tendinopathy", "https://www.ncbi.nlm.nih.gov/books/NBK532270/")
        ]
    },
    {
        "file": "biceps_tendinopathy.md",
        "id": "COND_BICEPS_TENDINOPATHY",
        "name": "Biceps Tendinopathy (Long Head)",
        "category": "Shoulder",
        "mechanism": "Repetitive traction or friction of the long head of the biceps tendon within the bicipital groove of the humerus, often secondary to glenohumeral instability or anterior impingement.",
        "contraindications": [
            "Preacher curls with hyper-extended elbows",
            "Incline dumbbell curls with excessive shoulder extension",
            "Heavy underhand (supinated) chin-ups extending to full arm lock-out"
        ],
        "modifications": [
            "Maintain neutral wrist/forearm position (hammer grip) during elbow flexion movements",
            "Avoid deep shoulder extension during curls and pulling movements",
            "Limit shoulder anterior translation during pressing and pulling"
        ],
        "substitutions": [
            "Neutral-grip hammer curls instead of supinated preacher curls",
            "Neutral-grip cable pulldowns instead of underhand supinated chin-ups",
            "Rope cable hammer curls with controlled range of motion"
        ],
        "sources": [
            ("Physiopedia - Biceps Tendinopathy", "https://www.physio-pedia.com/Biceps_Tendinopathy"),
            ("NCBI StatPearls - Biceps Tendonitis", "https://www.ncbi.nlm.nih.gov/books/NBK519000/")
        ]
    },
    {
        "file": "anterior_shoulder_instability.md",
        "id": "COND_ANTERIOR_SHOULDER_INSTABILITY",
        "name": "Anterior Shoulder Instability",
        "category": "Shoulder",
        "mechanism": "Laxity or disruption of the anterior glenohumeral capsule and labrum (e.g., Bankart lesion), making the humeral head prone to subluxation during combined abduction and external rotation (high-five position).",
        "contraindications": [
            "Barbell neck press or overhead pressing behind the head",
            "Behind-the-head lat pulldowns",
            "Heavy dumbbell chest flyes with deep arm abduction and external rotation",
            "Dips with shoulder extension past neutral"
        ],
        "modifications": [
            "Never position the humerus in abduction (>90 degrees) combined with passive external rotation",
            "Keep all pressing movements anterior to the coronal plane",
            "Limit horizontal abduction so elbows do not pass behind the plane of the torso"
        ],
        "substitutions": [
            "Floor dumbbell press instead of flat dumbbell flyes",
            "Anterior cable pulldowns to chest instead of behind-the-neck pulldowns",
            "Landmine press with neutral grip instead of overhead barbell press"
        ],
        "sources": [
            ("Physiopedia - Anterior Shoulder Instability", "https://www.physio-pedia.com/Anterior_Shoulder_Instability"),
            ("NCBI StatPearls - Anterior Shoulder Instability", "https://www.ncbi.nlm.nih.gov/books/NBK538221/")
        ]
    },
    {
        "file": "adhesive_capsulitis.md",
        "id": "COND_ADHESIVE_CAPSULITIS",
        "name": "Adhesive Capsulitis (Frozen Shoulder)",
        "category": "Shoulder",
        "mechanism": "Fibrotic thickening and contracture of the glenohumeral joint capsule, restricting active and passive range of motion across all planes, particularly external rotation and abduction.",
        "contraindications": [
            "Aggressive end-range ballistic shoulder stretching under heavy load",
            "Heavy overhead barbell presses requiring full active ROM",
            "Kipping pull-ups or explosive hanging movements"
        ],
        "modifications": [
            "Perform strength exercises strictly within pain-free available range of motion",
            "Utilize submaximal isometric contractions near available ROM boundaries",
            "Maintain neutral shoulder positioning and avoid forced end-range leverage"
        ],
        "substitutions": [
            "Low-cable standing rows within comfortable ROM instead of heavy barbell rows",
            "Dumbbell chest-supported press restricted to painless ROM",
            "Scapular protraction/retraction drills (push-up plus) in neutral shoulder position"
        ],
        "sources": [
            ("Physiopedia - Adhesive Capsulitis", "https://www.physio-pedia.com/Adhesive_Capsulitis"),
            ("NCBI StatPearls - Adhesive Capsulitis", "https://www.ncbi.nlm.nih.gov/books/NBK532955/")
        ]
    },
    {
        "file": "slap_lesion.md",
        "id": "COND_SLAP_LESION",
        "name": "Superior Labrum Anterior to Posterior (SLAP) Lesion",
        "category": "Shoulder",
        "mechanism": "Tearing of the superior glenoid labrum near the attachment of the long head of the biceps tendon, triggered by traction forces, peel-back mechanism in external rotation, or overhead stress.",
        "contraindications": [
            "Heavy biceps curls with heavy eccentric loading (biceps traction)",
            "Kipping or high-repetition pull-ups with sudden bottom lock-out",
            "Overhead snatch or heavy overhead pressing with full shoulder extension/external rotation"
        ],
        "modifications": [
            "Avoid full elbow extension lock-out during biceps-dominant pulling movements",
            "Perform shoulder elevation strictly in the scapular plane with neutral hand positioning",
            "Avoid heavy eccentric loading of the biceps long head"
        ],
        "substitutions": [
            "Inverted rows with neutral grip instead of heavy overhead pull-ups",
            "Scaption dumbbell raises instead of heavy lateral or overhead raises",
            "Cable neutral-grip rows with limited shoulder extension"
        ],
        "sources": [
            ("Physiopedia - SLAP Lesion", "https://www.physio-pedia.com/SLAP_Lesion"),
            ("NCBI StatPearls - SLAP Lesions", "https://www.ncbi.nlm.nih.gov/books/NBK538283/")
        ]
    },

    # --- BACK (7) ---
    {
        "file": "lumbar_disc_herniation.md",
        "id": "COND_LUMBAR_DISC_HERNIATION",
        "name": "Lumbar Disc Herniation",
        "category": "Back",
        "mechanism": "Displacement of nucleus pulposus material through a torn annulus fibrosus in the lumbar spine, exacerbating mechanical compression and chemical irritation of nerve roots during spinal flexion and axial loading.",
        "contraindications": [
            "Loaded spinal flexion exercises (e.g., conventional Jefferson curls, weighted sit-ups)",
            "Heavy axial loading under spinal flexion (e.g., heavy conventional deadlifts, rounded-back squats)",
            "Machine torso rotation under heavy loads with spinal flexion"
        ],
        "modifications": [
            "Maintain rigid neutral spine bracing throughout all compound lifts",
            "Prefer spinal extension/neutral positions over spinal flexion",
            "Reduce axial compressive load on the lumbar spine by switching to unilateral or body-supported exercises"
        ],
        "substitutions": [
            "Chest-supported T-bar row instead of heavy bent-over barbell row",
            "Goblet squat or hip belt squat instead of heavy axial back squat",
            "Pallof press and stir-the-pot for anti-rotation core stability instead of sit-ups"
        ],
        "sources": [
            ("Physiopedia - Lumbar Disc Herniation", "https://www.physio-pedia.com/Lumbar_Disc_Herniation"),
            ("NCBI StatPearls - Lumbar Disc Herniation", "https://www.ncbi.nlm.nih.gov/books/NBK441822/")
        ]
    },
    {
        "file": "cervical_strain.md",
        "id": "COND_CERVICAL_STRAIN",
        "name": "Cervical Spine Strain",
        "category": "Back",
        "mechanism": "Overstretching or tearing of paraspinous muscles and tendons in the neck region, often aggravated by sudden neck extension, heavy shrugging, or poor forward-head posture under axial load.",
        "contraindications": [
            "Behind-the-head neck harness extensions under heavy load",
            "Heavy barbell shrugs with forward head posture",
            "Bridging on the head/neck (wrestler bridges)"
        ],
        "modifications": [
            "Maintain a neutral cervical spine (chin tucked, head inline with torso) during all exercises",
            "Avoid shrugging or hyperextending the neck at the top of deadlifts or presses",
            "Limit neck rotation under resistance"
        ],
        "substitutions": [
            "Chest-supported rows keeping chin tucked instead of heavy standing shrugs",
            "Isometric neck flexor/extensor holds against light hand resistance",
            "Neutral-grip dumbbell rows with head supported on an incline bench"
        ],
        "sources": [
            ("Physiopedia - Cervical Strain", "https://www.physio-pedia.com/Cervical_Strain"),
            ("NCBI StatPearls - Cervical Strain", "https://www.ncbi.nlm.nih.gov/books/NBK541081/")
        ]
    },
    {
        "file": "lumbar_facet_syndrome.md",
        "id": "COND_LUMBAR_FACET_SYNDROME",
        "name": "Lumbar Facet Joint Syndrome",
        "category": "Back",
        "mechanism": "Degeneration, inflammation, or mechanical impingement of the lumbar zygapophyseal joints, aggravated by hyperextension, rotation, and compressive axial loading.",
        "contraindications": [
            "Hyperextension movements under load (e.g., weighted back extensions into hyper-lordosis)",
            "Standing overhead presses executed with excessive lumbar arching",
            "Heavy standing rotatory exercises into lumbar extension"
        ],
        "modifications": [
            "Avoid hyperextending the lumbar spine; keep pelvis in neutral to slight posterior tilt",
            "Avoid combining spinal extension with rotation",
            "Use seated or supported postures to eliminate extension moments"
        ],
        "substitutions": [
            "Seated cable chest press instead of standing overhead press with back arching",
            "Bird-dog with neutral spine instead of GHD back extension into hyperextension",
            "Reverse hyper with controlled ROM focusing on glute engagement without arching"
        ],
        "sources": [
            ("Physiopedia - Facet Joint Syndrome", "https://www.physio-pedia.com/Facet_Joint_Syndrome"),
            ("NCBI StatPearls - Lumbar Facet Joint Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK570566/")
        ]
    },
    {
        "file": "sacroiliac_joint_dysfunction.md",
        "id": "COND_SACROILIAC_JOINT_DYSFUNCTION",
        "name": "Sacroiliac (SI) Joint Dysfunction",
        "category": "Back",
        "mechanism": "Altered neuromusculoskeletal mechanics or micro-hypermobility at the sacroiliac joint, leading to localized inflammation and shearing pain during asymmetrical pelvic loading.",
        "contraindications": [
            "Extreme asymmetrical loading with poor stability (e.g., heavy walking lunges with torso twisting)",
            "Single-leg deadlifts without pelvic stabilization",
            "Conventional deadlifts performed with pelvic asymmetry or rotation"
        ],
        "modifications": [
            "Keep feet symmetrically planted for heavy lifting (bilateral stance)",
            "Engage deep core bracing (transverse abdominis and pelvic floor) prior to initiating hip hinge",
            "Limit stride length on split squats to prevent excessive pelvic anterior/posterior shearing"
        ],
        "substitutions": [
            "Bilateral trap bar deadlift instead of asymmetrical single-leg stiff-leg deadlift",
            "Supported split squat holding onto a rack for stability instead of dynamic walking lunges",
            "Glute bridge with a resistance band around knees (pelvic stabilization)"
        ],
        "sources": [
            ("Physiopedia - Sacroiliac Joint Dysfunction", "https://www.physio-pedia.com/Sacroiliac_Joint_Dysfunction"),
            ("NCBI StatPearls - Sacroiliac Joint Dysfunction", "https://www.ncbi.nlm.nih.gov/books/NBK470299/")
        ]
    },
    {
        "file": "thoracic_outlet_syndrome.md",
        "id": "COND_THORACIC_OUTLET_SYNDROME",
        "name": "Thoracic Outlet Syndrome (TOS)",
        "category": "Back",
        "mechanism": "Compression of neurovascular structures (brachial plexus, subclavian vessels) within the interscalene triangle, costoclavicular space, or subcoracoid tunnel during overhead elevation or shoulder depression/retraction.",
        "contraindications": [
            "Heavy farmer's walks with heavy downward traction on shoulders",
            "Overhead pressing with extreme neck lateral flexion",
            "Prolonged heavy chest flies stretching the pectoralis minor forcefully"
        ],
        "modifications": [
            "Avoid heavy passive downward shoulder depression under heavy load",
            "Keep shoulder girdle elevated slightly rather than fully depressed during carry movements",
            "Avoid hyper-abduction of arms overhead when symptoms flare"
        ],
        "substitutions": [
            "Trap bar carry with light weight focused on active scapular positioning",
            "Incline bench dumbbell press in scapular plane",
            "Scapular wall slides prioritizing serratus anterior activation"
        ],
        "sources": [
            ("Physiopedia - Thoracic Outlet Syndrome", "https://www.physio-pedia.com/Thoracic_Outlet_Syndrome"),
            ("NCBI StatPearls - Thoracic Outlet Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK470183/")
        ]
    },
    {
        "file": "lumbar_spondylolisthesis.md",
        "id": "COND_LUMBAR_SPONDYLOLISTHESIS",
        "name": "Lumbar Spondylolisthesis",
        "category": "Back",
        "mechanism": "Anterior displacement of one vertebral body relative to the inferior vertebra (often secondary to pars interarticularis defect), aggravated by lumbar hyperextension and high shear forces.",
        "contraindications": [
            "Lumbar hyperextension exercises (e.g., cobra pose, standing back extensions)",
            "Heavy axial compressive loading with spinal extension (e.g., heavy overhead press standing)",
            "High-impact plyometrics with spinal arching"
        ],
        "modifications": [
            "Maintain a strict neutral-to-slightly flexed lumbar alignment",
            "Prioritize abdominal bracing and anterior core strength to prevent lumbar shear",
            "Use chest-supported or seated loading positions to minimize axial spinal shear"
        ],
        "substitutions": [
            "Dead-bug core bracing drills instead of back extension machines",
            "Chest-supported dumbbell row instead of standing bent-over barbell row",
            "Seated cable shoulder press with back supported instead of standing barbell press"
        ],
        "sources": [
            ("Physiopedia - Spondylolisthesis", "https://www.physio-pedia.com/Spondylolisthesis"),
            ("NCBI StatPearls - Spondylolisthesis", "https://www.ncbi.nlm.nih.gov/books/NBK430764/")
        ]
    },
    {
        "file": "lumbar_spinal_stenosis.md",
        "id": "COND_LUMBAR_SPINAL_STENOSIS",
        "name": "Lumbar Spinal Stenosis",
        "category": "Back",
        "mechanism": "Narrowing of the central spinal canal or neural foramina, leading to vascular or mechanical compression of spinal nerves, typically exacerbated by extension and relieved by slight spinal flexion.",
        "contraindications": [
            "Prolonged standing spinal extension",
            "Heavy axial loading in extension (e.g., back squat with pronounced lordosis)",
            "Prone back extensions"
        ],
        "modifications": [
            "Adopt a slight flexion-bias during hip hinging and lower body movements",
            "Perform seated or incline cycling exercises instead of standing upright extension movements",
            "Maintain abdominal hollow/posterior pelvic tilt during exercises"
        ],
        "substitutions": [
            "Incline leg press with controlled depth instead of heavy standing back squat",
            "Seated cable rowing instead of standing bent-over row",
            "Cat-cow (flexion emphasis) and curl-ups for core endurance"
        ],
        "sources": [
            ("Physiopedia - Lumbar Spinal Stenosis", "https://www.physio-pedia.com/Lumbar_Spinal_Stenosis"),
            ("NCBI StatPearls - Lumbar Spinal Stenosis", "https://www.ncbi.nlm.nih.gov/books/NBK482456/")
        ]
    },

    # --- KNEE (7) ---
    {
        "file": "patellar_tendinopathy.md",
        "id": "COND_PATELLAR_TENDINOPATHY",
        "name": "Patellar Tendinopathy (Jumper's Knee)",
        "category": "Knee",
        "mechanism": "Overload and degenerative changes in the patellar tendon near the inferior pole of the patella, provoked by rapid rate of force development (RFD), deep knee flexion, and high eccentric quadriceps decelerations.",
        "contraindications": [
            "High-impact plyometric depth jumps or bounding",
            "Rapid sissy squats or heavy deep knees-over-toes squats under high load",
            "Ballistic jump squats with uncontrolled landing"
        ],
        "modifications": [
            "Use slow heavy resistance (isometric or slow isotonic 3-4s tempo) to promote tendon remodeling",
            "Restrict peak knee flexion angle during acute flare-ups (e.g., box squats to 90 degrees)",
            "Ensure shin angle is kept relatively vertical during heavy squatting to reduce patellar tendon shear"
        ],
        "substitutions": [
            "Spanish squats (with strap behind knees) for heavy isometric patellar loading",
            "Box squats to parallel with slow controlled tempo instead of dynamic jump squats",
            "Romanian deadlifts (posterior chain emphasis) to balance knee-dominant quadriceps stress"
        ],
        "sources": [
            ("Physiopedia - Patellar Tendinopathy", "https://www.physio-pedia.com/Patellar_Tendinopathy"),
            ("NCBI StatPearls - Patellar Tendonitis", "https://www.ncbi.nlm.nih.gov/books/NBK519014/")
        ]
    },
    {
        "file": "patellofemoral_pain_syndrome.md",
        "id": "COND_PATELLOFEMORAL_PAIN_SYNDROME",
        "name": "Patellofemoral Pain Syndrome (PFPS)",
        "category": "Knee",
        "mechanism": "Abnormal tracking of the patella within the trochlear groove of the femur, increasing retropatellar contact stress during deep knee flexion, aggravated by weak gluteals and quadriceps imbalanced pull.",
        "contraindications": [
            "Open kinetic chain knee extensions from 90 to 0 degrees under heavy load",
            "Deep lunges where the knee collapses medially (valgus collapse)",
            "Step-downs from high boxes without hip stabilization"
        ],
        "modifications": [
            "Limit open-chain knee extensions to 50-0 degrees or perform closed-chain squats from 0-45 degrees ROM",
            "Ensure knee tracks strictly over the second/third toe, eliminating dynamic valgus",
            "Strengthen hip abductors and external rotators to stabilize patellofemoral alignment"
        ],
        "substitutions": [
            "Leg press limited to 0-60 degrees knee flexion instead of deep open-chain leg extensions",
            "Step-ups onto a low box with band around knees to encourage hip abduction",
            "Clamshells and lateral band walks for hip abductor strengthening"
        ],
        "sources": [
            ("Physiopedia - Patellofemoral Pain Syndrome", "https://www.physio-pedia.com/Patellofemoral_Pain_Syndrome"),
            ("NCBI StatPearls - Patellofemoral Pain Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK557657/")
        ]
    },
    {
        "file": "acl_sprain.md",
        "id": "COND_ACL_SPRAIN",
        "name": "Anterior Cruciate Ligament (ACL) Sprain / Deficiency",
        "category": "Knee",
        "mechanism": "Disruption or tearing of the ACL due to excessive anterior tibial translation, dynamic knee valgus, and internal rotation, destabilizing the tibiofemoral joint.",
        "contraindications": [
            "Heavy open kinetic chain leg extensions near full knee extension (30-0 degrees)",
            "Uncontrolled pivoting, cutting, or lateral jumping without stabilization",
            "Deep squatting with uncontrolled valgus collapse"
        ],
        "modifications": [
            "Focus on closed kinetic chain exercises where hamstrings co-contract to reduce anterior tibial translation",
            "Ensure strict knee-to-toe alignment without inward knee collapse",
            "Perform controlled tempo movements avoiding rapid deceleration/pivoting"
        ],
        "substitutions": [
            "Romanian deadlifts and hamstring curls (hamstrings act as ACL synergists)",
            "Bilateral leg press with controlled ROM instead of open-chain knee extensions",
            "Glute bridges and hip thrusts for posterior chain reinforcement"
        ],
        "sources": [
            ("Physiopedia - Anterior Cruciate Ligament Injury", "https://www.physio-pedia.com/Anterior_Cruciate_Ligament_(ACL)_Injury"),
            ("NCBI StatPearls - Anterior Cruciate Ligament Tear", "https://www.ncbi.nlm.nih.gov/books/NBK499848/")
        ]
    },
    {
        "file": "meniscal_tear.md",
        "id": "COND_MENISCAL_TEAR",
        "name": "Meniscal Tear",
        "category": "Knee",
        "mechanism": "Fissuring or disruption of fibrocartilaginous meniscus tissue caused by loaded twisting, pivoting, or extreme deep hyper-flexion of the knee joint.",
        "contraindications": [
            "Deep squatting below parallel (hyper-flexion under heavy load)",
            "Loaded twisting/pivoting on a planted foot (e.g., rotational lunges)",
            "Heavy leg press at full knee extension lock-out or deep flexion end-range"
        ],
        "modifications": [
            "Limit knee flexion range of motion to 0-90 degrees to avoid pinching posterior horn of meniscus",
            "Keep feet pointing straight and pivot using hips/torso together rather than twisting planted knee",
            "Avoid high-impact jumping or landing"
        ],
        "substitutions": [
            "Parallel box squat (restricted to 90 degrees) instead of ass-to-grass deep squat",
            "Straight-leg deadlifts / RDLs keeping knee flexion minimal",
            "Seated hamstring curls with light-to-moderate controlled load"
        ],
        "sources": [
            ("Physiopedia - Meniscal Lesions", "https://www.physio-pedia.com/Meniscal_Lesions"),
            ("NCBI StatPearls - Meniscal Tear", "https://www.ncbi.nlm.nih.gov/books/NBK430784/")
        ]
    },
    {
        "file": "iliotibial_band_syndrome.md",
        "id": "COND_ILIOTIBIAL_BAND_SYNDROME",
        "name": "Iliotibial (IT) Band Syndrome",
        "category": "Knee",
        "mechanism": "Compression and friction of the distal IT band against the lateral femoral epicondyle during repeated knee flexion-extension around 30 degrees of knee angle.",
        "contraindications": [
            "High-volume repetitive downhill running or step-downs",
            "Deep cross-over lunges (curtsy lunges) exaggerating hip adduction",
            "Heavy leg press with narrow stance encouraging adduction"
        ],
        "modifications": [
            "Adopt a slightly wider stance on squats and leg press to prevent hip adduction",
            "Strengthen gluteus medius to eliminate contralateral pelvic drop",
            "Avoid working excessively in the 20-30 degree knee flexion friction zone under high volume"
        ],
        "substitutions": [
            "Side-lying hip abduction with internal/neutral rotation instead of curtsy lunges",
            "Wide-stance sumo deadlift or box squat instead of narrow-stance squat",
            "Monster walks with resistance loop around knees"
        ],
        "sources": [
            ("Physiopedia - Iliotibial Band Syndrome", "https://www.physio-pedia.com/Iliotibial_Band_Syndrome"),
            ("NCBI StatPearls - Iliotibial Band Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK542185/")
        ]
    },
    {
        "file": "mcl_sprain.md",
        "id": "COND_MCL_SPRAIN",
        "name": "Medial Collateral Ligament (MCL) Sprain",
        "category": "Knee",
        "mechanism": "Valgus stress or lateral blow to the knee causing overstretching or tearing of the medial collateral ligament fibers on the inner aspect of the joint.",
        "contraindications": [
            "Wide-stance sumo squats or side lunges inducing valgus torque",
            "Breaststroke kicking or lateral cutting movements",
            "Any exercise permitting dynamic knee valgus collapse"
        ],
        "modifications": [
            "Use a shoulder-width parallel stance with knees tracking strictly over toes",
            "Avoid lateral or frontal-plane twisting forces on the knee joint",
            "Limit movement strictly to sagittal plane (pure extension/flexion)"
        ],
        "substitutions": [
            "Standard bilateral machine leg press with parallel feet placement",
            "Straight-leg calf raises and hamstring leg curls in pure sagittal plane",
            "Standard sagittal step-ups with low step height"
        ],
        "sources": [
            ("Physiopedia - Medial Collateral Ligament Injury of the Knee", "https://www.physio-pedia.com/Medial_Collateral_Ligament_Injury_of_the_Knee"),
            ("NCBI StatPearls - Medial Collateral Ligament Knee Injuries", "https://www.ncbi.nlm.nih.gov/books/NBK430910/")
        ]
    },
    {
        "file": "pes_anserine_bursitis.md",
        "id": "COND_PES_ANSERINE_BURSITIS",
        "name": "Pes Anserine Bursitis",
        "category": "Knee",
        "mechanism": "Inflammation of the bursa underlying the pes anserinus tendon insertion (sartorius, gracilis, semitendinosus) on the anteromedial proximal tibia, caused by friction and valgus knee stress.",
        "contraindications": [
            "Heavy seated hamstring curls into full flexion with internal tibial rotation",
            "Deep wide-stance squats aggravating medial tendon friction",
            "Repetitive lateral bounding into knee valgus"
        ],
        "modifications": [
            "Avoid deep end-range knee flexion under heavy resistance",
            "Maintain strict sagittal knee-over-toe tracking, preventing medial knee deviation",
            "Limit high-repetition hamstring loading during acute inflammation"
        ],
        "substitutions": [
            "Straight-leg glute-ham raises or hip thrusts emphasizing glute engagement",
            "Parallel box squats with neutral knee alignment",
            "Standing calf raises in neutral stance"
        ],
        "sources": [
            ("Physiopedia - Pes Anserine Bursitis", "https://www.physio-pedia.com/Pes_Anserine_Bursitis"),
            ("NCBI StatPearls - Pes Anserine Bursitis", "https://www.ncbi.nlm.nih.gov/books/NBK532941/")
        ]
    },

    # --- ELBOW (6) ---
    {
        "file": "medial_epicondylitis.md",
        "id": "COND_MEDIAL_EPICONDYLITIS",
        "name": "Medial Epicondylitis (Golfer's Elbow)",
        "category": "Elbow",
        "mechanism": "Micro-trauma and angiofibroblastic tendinosis at the common flexor-pronator origin on the medial epicondyle of the humerus, caused by repetitive wrist flexion and forearm pronation under load.",
        "contraindications": [
            "Heavy wrist curls into full flexion under heavy load",
            "Heavy underhand (supinated) lat pulldowns or chin-ups",
            "Aggressive forearm pronation exercises under heavy resistance"
        ],
        "modifications": [
            "Use neutral grip (palms facing each other) or use lifting straps to reduce grip/wrist flexor demand",
            "Avoid full end-range wrist flexion during pulling exercises",
            "Utilize submaximal eccentric wrist extension/flexion loading protocols for tendon rehabilitation"
        ],
        "substitutions": [
            "Neutral-grip cable rows with lifting straps instead of supinated barbell rows",
            "Dumbbell hammer curls instead of heavy supinated barbell curls",
            "Chest-supported row using neutral handles"
        ],
        "sources": [
            ("Physiopedia - Medial Epicondylitis", "https://www.physio-pedia.com/Medial_Epicondylitis"),
            ("NCBI StatPearls - Medial Epicondylitis", "https://www.ncbi.nlm.nih.gov/books/NBK507000/")
        ]
    },
    {
        "file": "lateral_epicondylitis.md",
        "id": "COND_LATERAL_EPICONDYLITIS",
        "name": "Lateral Epicondylitis (Tennis Elbow)",
        "category": "Elbow",
        "mechanism": "Micro-tearing and tendinosis at the common extensor origin (primarily extensor carpi radialis brevis) on the lateral epicondyle, provoked by repetitive wrist extension and forceful gripping.",
        "contraindications": [
            "Heavy overhand (pronated) barbell biceps curls (reverse curls)",
            "Heavy overhand wrist extension curls under load",
            "Heavy deadlifts without wrist straps causing excessive finger extensor static stabilization"
        ],
        "modifications": [
            "Utilize lifting straps to offload wrist extensors during heavy deadlifts and pulls",
            "Adopt a neutral or supinated grip position to reduce extensor tendon tension",
            "Avoid gripping objects tightly with an extended wrist position"
        ],
        "substitutions": [
            "Supinated dumbbell curls instead of pronated reverse curls",
            "Deadlifts using wrist straps to eliminate forceful gripping tension",
            "Cable lat pulldowns with neutral V-bar handle"
        ],
        "sources": [
            ("Physiopedia - Lateral Epicondylitis", "https://www.physio-pedia.com/Lateral_Epicondylitis"),
            ("NCBI StatPearls - Lateral Epicondylitis", "https://www.ncbi.nlm.nih.gov/books/NBK430725/")
        ]
    },
    {
        "file": "olecranon_bursitis.md",
        "id": "COND_OLECRANON_BURSITIS",
        "name": "Olecranon Bursitis",
        "category": "Elbow",
        "mechanism": "Inflammation and fluid accumulation within the olecranon bursa between the posterior tip of the ulna and the skin, triggered by direct trauma, pressure, or repetitive friction.",
        "contraindications": [
            "Planks resting directly on hard elbows",
            "Triceps bench dips resting weight directly on olecranon tip",
            "Any exercise applying direct compression/impact to the posterior elbow"
        ],
        "modifications": [
            "Perform plank variations resting on forearms with thick foam padding or on hands (high plank)",
            "Avoid direct resting of elbows on benches or hard surfaces during exercises",
            "Keep elbow flexion/extension smooth without slamming end-range extension"
        ],
        "substitutions": [
            "High push-up planks on hands instead of low forearm planks",
            "Cable standing triceps pushdowns instead of bench dips resting on hands/elbows",
            "Dumbbell chest press with padded elbow position"
        ],
        "sources": [
            ("Physiopedia - Olecranon Bursitis", "https://www.physio-pedia.com/Olecranon_Bursitis"),
            ("NCBI StatPearls - Olecranon Bursitis", "https://www.ncbi.nlm.nih.gov/books/NBK557813/")
        ]
    },
    {
        "file": "distal_biceps_tendinopathy.md",
        "id": "COND_DISTAL_BICEPS_TENDINOPATHY",
        "name": "Distal Biceps Tendinopathy",
        "category": "Elbow",
        "mechanism": "Degenerative changes and micro-tears at the distal insertion of the biceps brachii tendon onto the radial tuberosity, aggravated by heavy eccentric loading in supination.",
        "contraindications": [
            "Heavy eccentric biceps curls into full elbow extension lock-out",
            "Overhand mixed-grip deadlifts on the supinated arm side",
            "Ballistic heavy chin-ups with rapid bottom drop-out"
        ],
        "modifications": [
            "Avoid full passive elbow extension lock-out under load",
            "Perform deadlifts with double-overhand grip + straps or hook grip to avoid asymmetrical biceps load",
            "Use neutral hammer grip to reduce tensile stress on radial tuberosity insertion"
        ],
        "substitutions": [
            "Hammer curls stopping 10 degrees short of full elbow lock-out",
            "Double-overhand strap deadlifts instead of mixed-grip deadlifts",
            "Cable neutral-grip pulldowns with controlled tempo"
        ],
        "sources": [
            ("Physiopedia - Distal Biceps Tendon Injury", "https://www.physio-pedia.com/Distal_Biceps_Tendon_Injury"),
            ("NCBI StatPearls - Distal Biceps Tendon Rupture / Tendinopathy", "https://www.ncbi.nlm.nih.gov/books/NBK559105/")
        ]
    },
    {
        "file": "triceps_tendinopathy.md",
        "id": "COND_TRICEPS_TENDINOPATHY",
        "name": "Triceps Tendinopathy",
        "category": "Elbow",
        "mechanism": "Degeneration or inflammation of the triceps tendon at its insertion on the olecranon process of the ulna, caused by forceful repetitive extension or rapid eccentric deceleration.",
        "contraindications": [
            "French presses or skull crushers with deep elbow flexion and rapid lockout",
            "Heavy weighted dips extending into deep shoulder/elbow flexion",
            "Plyometric push-ups with explosive elbow extension"
        ],
        "modifications": [
            "Limit maximum elbow flexion angle to 90 degrees during triceps extensions",
            "Use cable pushdowns with rope attachment to allow natural joint path without rigid joint forcing",
            "Avoid rapid lock-out or hyper-extending the elbow joint at peak contraction"
        ],
        "substitutions": [
            "Cable rope triceps pushdowns with 90-degree flexion limit instead of skull crushers",
            "Close-grip bench press with controlled tempo on a flat bench",
            "Towel push-ups with limited ROM"
        ],
        "sources": [
            ("Physiopedia - Triceps Tendinopathy", "https://www.physio-pedia.com/Triceps_Tendinopathy"),
            ("NCBI StatPearls - Triceps Tendon Injuries", "https://www.ncbi.nlm.nih.gov/books/NBK537084/")
        ]
    },
    {
        "file": "cubital_tunnel_syndrome.md",
        "id": "COND_CUBITAL_TUNNEL_SYNDROME",
        "name": "Cubital Tunnel Syndrome",
        "category": "Elbow",
        "mechanism": "Traction or compression of the ulnar nerve within the cubital tunnel on the medial aspect of the elbow, exacerbated by prolonged deep elbow flexion and direct pressure.",
        "contraindications": [
            "High-repetition deep-flexion triceps extensions held in full bend",
            "Heavy preacher curls resting medial elbow directly on hard pad under heavy load",
            "Prolonged isometric holds in end-range elbow flexion"
        ],
        "modifications": [
            "Avoid maintaining elbow flexion greater than 90 degrees for extended periods",
            "Ensure arm pads do not press directly into the medial epicondylar groove",
            "Maintain neutral wrist alignment and avoid combined wrist flexion + elbow flexion end-range"
        ],
        "substitutions": [
            "Standing cable triceps pushdowns working between 30 and 90 degrees elbow flexion",
            "Incline dumbbell curls with arm hanging naturally (no pad pressure on cubital tunnel)",
            "Standing dumbbell shoulder press with neutral grip"
        ],
        "sources": [
            ("Physiopedia - Cubital Tunnel Syndrome", "https://www.physio-pedia.com/Cubital_Tunnel_Syndrome"),
            ("NCBI StatPearls - Cubital Tunnel Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK482259/")
        ]
    },

    # --- HIP (7) ---
    {
        "file": "hamstring_strain.md",
        "id": "COND_HAMSTRING_STRAIN",
        "name": "Hamstring Muscle Strain",
        "category": "Hip",
        "mechanism": "Acute tear or micro-damage of the hamstring muscle complex (biceps femoris, semitendinosus, semimembranosus) during rapid eccentric lengthening at the hip or knee during terminal swing or heavy hip hinging.",
        "contraindications": [
            "Heavy Jefferson curls or maximum end-range hamstring stretching under load",
            "Explosive sprinting or high-velocity sprinting strides during recovery phase",
            "Maximum weight straight-leg deadlifts with rounded lower back"
        ],
        "modifications": [
            "Limit hip flexion angle when knee is fully extended during early rehabilitation",
            "Utilize progressive submaximal eccentric loading (e.g., Nordic hamstring curls) at controlled speeds",
            "Keep knee slightly bent during hip hinging movements to decrease distal tendon strain"
        ],
        "substitutions": [
            "Glute bridge with feet close to hips instead of deep Romanian deadlifts",
            "Swiss ball hamstring curls with controlled range of motion",
            "Isometric single-leg bridge holds"
        ],
        "sources": [
            ("Physiopedia - Hamstring Strain", "https://www.physio-pedia.com/Hamstring_Strain"),
            ("NCBI StatPearls - Hamstring Injuries", "https://www.ncbi.nlm.nih.gov/books/NBK558940/")
        ]
    },
    {
        "file": "greater_trochanteric_pain_syndrome.md",
        "id": "COND_GREATER_TROCHANTERIC_PAIN_SYNDROME",
        "name": "Greater Trochanteric Pain Syndrome (GTPS)",
        "category": "Hip",
        "mechanism": "Compression and recalcitrant tendinosis of the gluteus medius/minimus tendons and overlying trochanteric bursa against the greater trochanter during hip adduction.",
        "contraindications": [
            "Cross-body hip adduction stretches under load (e.g., IT band cross stretches)",
            "Single-leg squats where hip drops into adduction (Trendelenburg sign)",
            "Sleeping or side-lying exercises resting directly on the affected hip without padding"
        ],
        "modifications": [
            "Avoid exercises that force the hip past neutral into adduction",
            "Maintain a wider stance on squats and leg press to avoid compressive adduction",
            "Strengthen gluteals in isometric or short-lever abduction ranges without adduction end-range"
        ],
        "substitutions": [
            "Standing cable hip abduction (starting from neutral leg position, not crossed over)",
            "Bilateral hip thrusts with band around knees",
            "Step-ups onto a low platform focusing on level pelvis"
        ],
        "sources": [
            ("Physiopedia - Greater Trochanteric Pain Syndrome", "https://www.physio-pedia.com/Greater_Trochanteric_Pain_Syndrome"),
            ("NCBI StatPearls - Greater Trochanteric Bursitis", "https://www.ncbi.nlm.nih.gov/books/NBK557433/")
        ]
    },
    {
        "file": "femoroacetabular_impingement.md",
        "id": "COND_FEMOROACETABULAR_IMPINGEMENT",
        "name": "Femoroacetabular Impingement (FAI)",
        "category": "Hip",
        "mechanism": "Abnormal bony contact between the femoral head/neck (Cam) and/or acetabular rim (Pincer), causing labral damage and cartilage shear during deep hip flexion and internal rotation.",
        "contraindications": [
            "Ass-to-grass deep squats exceeding available pain-free hip flexion ROM",
            "Deep hip flexion combined with internal rotation (e.g., internal rotation seated leg press)",
            "High hurdle stretches or deep Olympic snatch squat catching positions"
        ],
        "modifications": [
            "Limit squat and hip flexion depth to above the point of pinch/impingement (typically parallel or higher)",
            "Turn toes slightly outward (external rotation 15-30 degrees) to clear femoral neck from acetabular rim",
            "Adopt a moderate-to-wide squat stance"
        ],
        "substitutions": [
            "Box squats set above hip impingement depth with externally rotated hip stance",
            "Hex bar (trap bar) deadlifts with moderate hip hinge ROM",
            "Glute thrusts focusing on hip extension without deep hip flexion end-range"
        ],
        "sources": [
            ("Physiopedia - Femoroacetabular Impingement", "https://www.physio-pedia.com/Femoroacetabular_Impingement"),
            ("NCBI StatPearls - Femoroacetabular Impingement", "https://www.ncbi.nlm.nih.gov/books/NBK544316/")
        ]
    },
    {
        "file": "hip_flexor_strain.md",
        "id": "COND_HIP_FLEXOR_STRAIN",
        "name": "Hip Flexor Strain (Iliopsoas / Rectus Femoris)",
        "category": "Hip",
        "mechanism": "Overstretching or violent forceful contraction of the iliopsoas or rectus femoris muscle complex, commonly occurring during explosive hip extension or high kicking.",
        "contraindications": [
            "Hanging leg raises with heavy eccentric lower and arched lower back",
            "Deep lunges with hyper-extended rear leg under heavy weight",
            "Explosive sprinting strides or high-kick drills"
        ],
        "modifications": [
            "Limit rear leg extension distance during lunges to maintain neutral pelvic posture",
            "Keep core braced and prevent anterior pelvic tilt during hip extension",
            "Reduce lever length during core flexion movements (bend knees)"
        ],
        "substitutions": [
            "Reverse planks or glute bridges for posterior chain strength without aggressive hip flexor stretch",
            "Seated knee tucks with controlled range of motion instead of hanging leg raises",
            "Step-ups onto low box with upright torso"
        ],
        "sources": [
            ("Physiopedia - Hip Flexor Strain", "https://www.physio-pedia.com/Hip_Flexor_Strain"),
            ("NCBI StatPearls - Hip Flexor Strain", "https://www.ncbi.nlm.nih.gov/books/NBK560608/")
        ]
    },
    {
        "file": "piriformis_syndrome.md",
        "id": "COND_PIRIFORMIS_SYNDROME",
        "name": "Piriformis Syndrome",
        "category": "Hip",
        "mechanism": "Neuromuscular condition where the piriformis muscle spasms or becomes tight, compressing the sciatic nerve as it passes beneath or through the muscle belly.",
        "contraindications": [
            "Heavy seated hip abductor machine squeezing into deep internal rotation",
            "Aggressive loaded hip rotation under heavy spinal load",
            "Prolonged static seated compression on hard surfaces"
        ],
        "modifications": [
            "Perform hip rotator strengthening within comfortable, non-symptomatic ranges",
            "Avoid deep passive stretching that reproduces sharp sciatic radicular symptoms",
            "Focus on gluteal strengthening to offload overburdened deep rotators"
        ],
        "substitutions": [
            "Bilateral glute bridges with neutral hip rotation",
            "Clamshells performed with slow controlled tempo and light band resistance",
            "Standing cable kickbacks in pure hip extension"
        ],
        "sources": [
            ("Physiopedia - Piriformis Syndrome", "https://www.physio-pedia.com/Piriformis_Syndrome"),
            ("NCBI StatPearls - Piriformis Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK448172/")
        ]
    },
    {
        "file": "adductor_strain.md",
        "id": "COND_ADDUCTOR_STRAIN",
        "name": "Adductor Muscle Strain (Groin Strain)",
        "category": "Hip",
        "mechanism": "Tensile rupture or tearing of adductor muscle fibers (adductor longus, magnus, brevis) caused by sudden directional changes, wide hip abduction, or forced external rotation.",
        "contraindications": [
            "Ultra-wide sumo deadlifts or sumo squats under heavy load",
            "Lateral side lunges into deep adductor end-range stretch",
            "Ballistic martial arts kicks or lateral jumping"
        ],
        "modifications": [
            "Narrow the stance width to hip-width or shoulder-width during squats and deadlifts",
            "Keep hip movement strictly in the sagittal plane, avoiding wide abduction",
            "Perform Copenhagen adductor exercises progressively starting from short-lever (knee) variations"
        ],
        "substitutions": [
            "Narrow-stance conventional deadlift or trap bar deadlift instead of sumo deadlift",
            "Standard sagittal split squat instead of lateral side lunge",
            "Short-lever Copenhagen side plank on knees"
        ],
        "sources": [
            ("Physiopedia - Adductor Strain", "https://www.physio-pedia.com/Adductor_Strain"),
            ("NCBI StatPearls - Adductor Longus Strain / Groin Injury", "https://www.ncbi.nlm.nih.gov/books/NBK559092/")
        ]
    },
    {
        "file": "gluteal_tendinopathy.md",
        "id": "COND_GLUTEAL_TENDINOPATHY",
        "name": "Gluteal Tendinopathy",
        "category": "Hip",
        "mechanism": "Tendinosis of the gluteus medius or minimus tendon insertions, driven by compressive forces against the greater trochanter during hip adduction and tensile load during weight-bearing.",
        "contraindications": [
            "Single-leg deadlifts with uncorrected hip drop into adduction",
            "IT-band cross-over stretches pulling hip into deep adduction",
            "Heavy lateral steps with excessive torso sway"
        ],
        "modifications": [
            "Avoid allowing the hip to enter adduction past the neutral midline",
            "Perform isometric glute abductor holds at 10-15 degrees of abduction",
            "Maintain pelvic levelness using external support during single-leg drills"
        ],
        "substitutions": [
            "Bilateral hip thrusts with band resistance above knees",
            "Isometric standing hip abduction against a wall",
            "Bilateral leg press with feet wide to avoid adduction stretch"
        ],
        "sources": [
            ("Physiopedia - Gluteal Tendinopathy", "https://www.physio-pedia.com/Gluteal_Tendinopathy"),
            ("NCBI StatPearls - Gluteus Medius Tendinopathy", "https://www.ncbi.nlm.nih.gov/books/NBK557433/")
        ]
    },

    # --- ANKLE (6) ---
    {
        "file": "plantar_fasciitis.md",
        "id": "COND_PLANTAR_FASCIITIS",
        "name": "Plantar Fasciitis",
        "category": "Ankle",
        "mechanism": "Micro-tearing and degenerative inflammation of the plantar fascia aponeurosis at its calcaneal insertion, provoked by high impact, excessive foot pronation, or sudden dorsiflexion load.",
        "contraindications": [
            "High-impact barefoot jumping or plyometrics",
            "Barefoot heavy calf raises into deep negative heel drop",
            "High-volume unconditioned running on hard concrete surfaces"
        ],
        "modifications": [
            "Wear supportive footwear with adequate arch support during all standing resistance training",
            "Avoid deep negative heel drops past neutral during calf raises in acute phases",
            "Utilize controlled eccentric calf loading with a towel under toes (windlass mechanism loading)"
        ],
        "substitutions": [
            "Seated calf raises limited to neutral heel depth instead of standing deep-drop calf raises",
            "Non-weight-bearing cardiorespiratory training (e.g., rowing or stationary bike) instead of running",
            "Controlled isometric calf holds at neutral foot angle"
        ],
        "sources": [
            ("Physiopedia - Plantar Fasciitis", "https://www.physio-pedia.com/Plantar_Fasciitis"),
            ("NCBI StatPearls - Plantar Fasciitis", "https://www.ncbi.nlm.nih.gov/books/NBK431073/")
        ]
    },
    {
        "file": "achilles_tendinopathy.md",
        "id": "COND_ACHILLES_TENDINOPATHY",
        "name": "Achilles Tendinopathy",
        "category": "Ankle",
        "mechanism": "Degenerative changes and failed healing response in the Achilles tendon (mid-substance or insertional) caused by excessive tensile strain, rapid plyometric loading, or sudden increase in training volume.",
        "contraindications": [
            "Explosive bounding or sprint starts",
            "Heavy insertional loading (deep negative calf drops) if insertional tendinopathy",
            "Ballistic jump rope skipping under fatigue"
        ],
        "modifications": [
            "Perform heavy slow resistance (HSR) eccentric-concentric calf raises on a flat surface (for insertional) or step (for mid-substance)",
            "Control movement tempo (3s eccentric, 3s concentric)",
            "Avoid sudden high-velocity ankle plantarflexion/dorsiflexion cycles"
        ],
        "substitutions": [
            "Heavy slow calf raises on floor (flat ground) instead of dynamic jump rope",
            "Seated soleus calf raises to vary tendon strain distribution",
            "Seated leg press calf extensions with controlled tempo"
        ],
        "sources": [
            ("Physiopedia - Achilles Tendinopathy", "https://www.physio-pedia.com/Achilles_Tendinopathy"),
            ("NCBI StatPearls - Achilles Tendonitis", "https://www.ncbi.nlm.nih.gov/books/NBK430857/")
        ]
    },
    {
        "file": "lateral_ankle_sprain.md",
        "id": "COND_LATERAL_ANKLE_SPRAIN",
        "name": "Lateral Ankle Sprain",
        "category": "Ankle",
        "mechanism": "Inversion and plantarflexion trauma causing tearing or stretching of the lateral ankle complex ligaments (anterior talofibular ligament ATFL, calcaneofibular ligament CFL).",
        "contraindications": [
            "Single-leg agility ladder drills on uneven surfaces during acute recovery",
            "Loaded split squats with foot rolling into inversion",
            "Plyometric lateral jumping without ankle bracing/taping"
        ],
        "modifications": [
            "Perform standing exercises with foot flat and stable ground contact",
            "Incorporate ankle semi-rigid bracing or taping during heavy standing lifts",
            "Focus on proprioceptive balance training on firm flat surfaces before unstable surfaces"
        ],
        "substitutions": [
            "Bilateral standing calf raises instead of single-leg unstable balance drills",
            "Seated leg press or machine squat instead of dynamic walking lunges",
            "Peroneal eversion isometric strengthening against resistance band"
        ],
        "sources": [
            ("Physiopedia - Ankle Sprain", "https://www.physio-pedia.com/Ankle_Sprain"),
            ("NCBI StatPearls - Ankle Sprain", "https://www.ncbi.nlm.nih.gov/books/NBK459212/")
        ]
    },
    {
        "file": "medial_tibial_stress_syndrome.md",
        "id": "COND_MEDIAL_TIBIAL_STRESS_SYNDROME",
        "name": "Medial Tibial Stress Syndrome (Shin Splints)",
        "category": "Ankle",
        "mechanism": "Traction periostitis along the posteromedial tibial border caused by repetitive impact loading and excessive fascial traction from the soleus, flexor digitorum longus, and posterior tibialis muscles.",
        "contraindications": [
            "High-impact plyometric box jumps on hard surfaces",
            "High-volume running with poor foot pronation control",
            "Repetitive weighted jump squats"
        ],
        "modifications": [
            "Transition to low-impact cardiorespiratory and resistance training",
            "Incorporate orthotics or supportive shoes to limit hyper-pronation",
            "Perform calf and tibialis anterior strengthening with controlled, non-ballistic tempo"
        ],
        "substitutions": [
            "Stationary bike or swimming for cardiovascular conditioning",
            "Seated calf raises and toe raises (tibialis anterior curls) with light load",
            "Bilateral leg press instead of weighted jump squats"
        ],
        "sources": [
            ("Physiopedia - Medial Tibial Stress Syndrome", "https://www.physio-pedia.com/Medial_Tibial_Stress_Syndrome"),
            ("NCBI StatPearls - Medial Tibial Stress Syndrome", "https://www.ncbi.nlm.nih.gov/books/NBK537241/")
        ]
    },
    {
        "file": "peroneal_tendinopathy.md",
        "id": "COND_PERONEAL_TENDINOPATHY",
        "name": "Peroneal Tendinopathy",
        "category": "Ankle",
        "mechanism": "Overuse injury or subluxation of the peroneal tendons (peroneus longus and brevis) behind the lateral malleolus, aggravated by repetitive eversion loading or excessive foot supination.",
        "contraindications": [
            "Heavy lateral cutting drills on slanted surfaces",
            "Calf raises with ankles rolling out into extreme inversion/supination",
            "Barefoot agility jumping on soft sand"
        ],
        "modifications": [
            "Ensure even weight distribution across the first and fifth metatarsal heads during standing lifts",
            "Avoid full passive inversion stretching under heavy axial load",
            "Perform controlled eccentric eversion exercises using resistance bands"
        ],
        "substitutions": [
            "Bilateral calf raises with a block between heels to prevent varus/inversion sway",
            "Seated leg press keeping feet flat and parallel",
            "Band eversion isometrics in neutral ankle position"
        ],
        "sources": [
            ("Physiopedia - Peroneal Tendinopathy", "https://www.physio-pedia.com/Peroneal_Tendinopathy"),
            ("NCBI StatPearls - Peroneal Tendonitis", "https://www.ncbi.nlm.nih.gov/books/NBK549794/")
        ]
    },
    {
        "file": "posterior_tibial_tendinopathy.md",
        "id": "COND_POSTERIOR_TIBIAL_TENDINOPATHY",
        "name": "Posterior Tibial Tendon Dysfunction (PTTD)",
        "category": "Ankle",
        "mechanism": "Progressive degeneration and lengthening of the posterior tibial tendon behind the medial malleolus, leading to loss of medial longitudinal arch support and flatfoot deformity under weight-bearing.",
        "contraindications": [
            "Heavy single-leg calf raises with severe uncorrected foot pronation/flatfoot collapse",
            "High-impact plyometrics without arch orthotics",
            "Barefoot heavy deadlifts or squats on collapsing arches"
        ],
        "modifications": [
            "Wear supportive orthotics or shoes with arch support during all loaded standing exercises",
            "Focus on active arch lifting ('short foot exercise') during squats and lunges",
            "Limit heavy standing calf raises until arch control and tendon capacity are restored"
        ],
        "substitutions": [
            "Short-foot arch activation drills in sitting and standing",
            "Seated leg press with orthotics to preserve medial arch height",
            "Inversion strengthening with band in neutral plantarflexion"
        ],
        "sources": [
            ("Physiopedia - Posterior Tibial Tendon Dysfunction", "https://www.physio-pedia.com/Posterior_Tibial_Tendon_Dysfunction"),
            ("NCBI StatPearls - Posterior Tibial Tendon Dysfunction", "https://www.ncbi.nlm.nih.gov/books/NBK542247/")
        ]
    }
]

def format_condition_md(c):
    lines = [
        f"# ID: {c['id']}",
        "",
        f"**Condition Name:** {c['name']}",
        "",
        f"**Category:** {c['category']}",
        "",
        f"**Mechanism of Irritation:** {c['mechanism']}",
        "",
        "## Absolute Contraindications (Exercises to Avoid)",
        ""
    ]
    for item in c['contraindications']:
        lines.append(f"* {item}")
    lines.append("")
    lines.append("## Biomechanical Modifications (Rules)")
    lines.append("")
    for item in c['modifications']:
        lines.append(f"* {item}")
    lines.append("")
    lines.append("## Recommended Substitutions")
    lines.append("")
    for item in c['substitutions']:
        lines.append(f"* {item}")
    lines.append("")
    lines.append("## Sources")
    lines.append("")
    for name, url in c['sources']:
        lines.append(f"* {name}")
        lines.append(f"* {url}")
    lines.append("")
    return "\n".join(lines)

def main():
    print(f"Generating {len(CONDITIONS)} clinical injury Markdown files in {OUTPUT_DIR}...")
    created_count = 0
    for c in CONDITIONS:
        filepath = OUTPUT_DIR / c['file']
        content = format_condition_md(c)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        created_count += 1
        print(f"Created: {filepath}")

    print(f"\nSuccessfully generated {created_count} condition files.")

if __name__ == "__main__":
    main()
