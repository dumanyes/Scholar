from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

biomed_skills = {
    "Medical Imaging": [
        "MRI", "CT Scan", "Ultrasound Imaging", "PET", "X-ray Imaging", "Image Reconstruction",
        "Radiomics", "Medical Image Segmentation", "Image Registration", "DICOM Standards",
        "3D Visualization", "Contrast Enhancement", "Functional Imaging", "Noise Reduction", "AI in Imaging"
    ],
    "Biomechanics": [
        "Kinematics", "Kinetics", "Gait Analysis", "Motion Capture", "Biomechanical Modeling",
        "Force Plate Analysis", "Finite Element Analysis", "Muscle Dynamics", "Joint Mechanics",
        "Posture Analysis", "Ergonomics", "Soft Tissue Mechanics", "Human Movement Science",
        "Orthopedic Biomechanics", "Rehabilitation Engineering"
    ],
    "Biomedical Signal Processing": [
        "ECG Analysis", "EEG Signal Processing", "EMG Analysis", "Signal Filtering", "Noise Reduction Techniques",
        "Wavelet Transform", "Fourier Analysis", "Feature Extraction", "Time-Frequency Analysis",
        "Artifact Removal", "Biomedical Sensors", "Digital Signal Processing", "QRS Detection", "Heart Rate Variability",
        "Machine Learning on Signals"
    ],
    "Wearable Sensors": [
        "Activity Monitoring", "Heart Rate Sensors", "Accelerometers", "Gyroscopes", "Smart Fabrics",
        "ECG Wearables", "Motion Sensors", "Real-Time Data Acquisition", "Battery Optimization",
        "Wireless Communication", "Data Synchronization", "Embedded Systems", "Sensor Calibration",
        "Body Area Networks", "Wearable Device Design"
    ],
    "Neuroengineering": [
        "Brain-Computer Interface", "Neural Signal Acquisition", "EEG/MEG Analysis", "Neuroimaging",
        "Neuroprosthetics", "Deep Brain Stimulation", "Neural Networks Modeling", "Neurostimulation",
        "Neural Decoding", "Electrophysiology", "Cognitive Neuroscience", "Functional Connectivity",
        "Neural Data Analysis", "Spiking Neural Networks", "Neurotechnology"
    ],
    "Biomaterials": [
        "Biodegradable Materials", "Polymeric Biomaterials", "Metallic Biomaterials", "Ceramics in Medicine",
        "Tissue Scaffolds", "Surface Modification", "Biocompatibility Testing", "Smart Biomaterials",
        "Drug Delivery Materials", "Nanomaterials", "Hydrogels", "Bioactive Glass", "Synthetic Polymers",
        "Natural Biomaterials", "Cell-Material Interaction"
    ],
    "Tissue Engineering": [
        "Scaffold Design", "Stem Cell Engineering", "Bioreactors", "Tissue Regeneration",
        "Cell Seeding Techniques", "Extracellular Matrix", "Hydrogels for Tissue Engineering",
        "Growth Factors", "3D Cell Culture", "Organ Printing", "Cartilage Engineering",
        "Skin Substitutes", "Tissue Vascularization", "Bone Tissue Engineering", "Decellularization"
    ],
    "Bioinstrumentation": [
        "Biosensors", "Signal Amplification", "Biomedical Transducers", "Data Acquisition Systems",
        "Sensor Interface Circuits", "Medical Device Prototyping", "Wireless Data Transfer",
        "Instrumentation Amplifiers", "Embedded Systems for Bio", "Biomedical Measurements",
        "Noise Minimization", "Analog to Digital Conversion", "Microcontrollers", "LabVIEW",
        "Real-Time Monitoring"
    ],
    "Biomedical Optics": [
        "Optical Coherence Tomography", "Fluorescence Imaging", "Biophotonics", "Spectroscopy",
        "Laser-Tissue Interaction", "Microscopy Techniques", "Optogenetics", "Photoacoustic Imaging",
        "Light Scattering", "Biomedical Lasers", "Fiber Optics", "Near-Infrared Spectroscopy",
        "Endoscopy", "Optical Biosensors", "Photodynamic Therapy"
    ],
    "Drug Delivery Systems": [
        "Controlled Release", "Nanoparticles", "Liposomes", "Targeted Delivery", "Pharmacokinetics",
        "Hydrogels for Delivery", "Inhalable Drugs", "Injectable Systems", "Transdermal Patches",
        "Oral Delivery Systems", "Biodegradable Carriers", "Drug-Polymer Interaction",
        "Implantable Delivery Devices", "Mucosal Delivery", "Microneedle Systems"
    ],
    "Rehabilitation Engineering": [
        "Prosthetics Design", "Orthotic Devices", "Assistive Technology", "Exoskeletons",
        "Rehabilitation Robotics", "Functional Electrical Stimulation", "Adaptive Equipment",
        "Motor Recovery Assessment", "Therapy Devices", "Motion Analysis in Rehab",
        "Sensor-Based Feedback", "User-Centered Design", "Speech Rehabilitation Tools",
        "Virtual Rehab Environments", "Accessibility Engineering"
    ],
    "Biorobotics": [
        "Bio-inspired Robots", "Robotic Surgery", "Micro Robots", "Soft Robotics", "Actuators in Bio",
        "Sensors in Biorobots", "Neural Interfaces", "Autonomous Rehab Devices", "Wearable Robotics",
        "Biomimetic Control", "Locomotion Mechanisms", "Medical Robotics", "Robotic Prosthetics",
        "Control Algorithms", "Biohybrid Systems"
    ],
    "Medical Device Design": [
        "Design Controls", "Usability Engineering", "Regulatory Requirements", "Risk Management",
        "Human Factors Engineering", "Prototyping", "Product Lifecycle", "Device Testing",
        "Design Verification", "Design Validation", "FDA Guidelines", "ISO Standards",
        "Device Classification", "Software as Medical Device", "Design Documentation"
    ],
    "Computational Physiology": [
        "Modeling Biological Systems", "Cardiac Modeling", "Respiratory Modeling", "Mathematical Biology",
        "Simulation Software", "Cellular Modeling", "Blood Flow Modeling", "Tissue Mechanics",
        "Multiscale Modeling", "Signal-Driven Models", "Biomechanical Simulations",
        "Parameter Estimation", "Electrophysiology Models", "ODEs/PDEs in Physiology",
        "Systems-Level Simulation"
    ],
    "3D Printing in Medicine": [
        "Bioprinting", "Medical Model Printing", "Custom Implants", "Tissue Scaffolds Printing",
        "Surgical Planning Tools", "Material Selection", "Anatomical Replication", "CAD Modeling",
        "Printing Resolution", "Post-Processing", "Multi-material Printing", "Regulatory Aspects",
        "Patient-Specific Devices", "Rapid Prototyping", "Sterilization of Prints"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in biomed_skills.items():
    subcat = SkillsSubCategory.objects.filter(name=subcat_name).first()
    if not subcat:
        missing_subcats.append(subcat_name)
        print(f"❌ Subcategory not found: {subcat_name}")
        continue

    print(f"\n📂 Processing subcategory: {subcat_name}")
    for skill_name in skill_list:
        try:
            obj, is_new = Skill.objects.get_or_create(name=skill_name, subcategory=subcat)
            if is_new:
                created += 1
                print(f"✅ Created: {skill_name}")
            else:
                skipped += 1
                print(f"⚠️ Already exists: {skill_name}")
        except IntegrityError:
            skipped += 1
            print(f"🚫 Integrity error (skipped): {skill_name}")

print("\n🎉 Import Complete!")
print(f"✅ Total created: {created}")
print(f"⚠️ Total skipped: {skipped}")
if missing_subcats:
    print("❌ Missing subcategories:")
    for subcat in missing_subcats:
        print(f" - {subcat}")
