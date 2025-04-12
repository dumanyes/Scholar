from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

env_sustainability_skills = {
    "Climate Modeling": [
        "Atmospheric Simulation", "General Circulation Models", "Climate Projections", "Downscaling", "Emission Scenarios",
        "Paleoclimate Reconstruction", "Climate Sensitivity", "Model Validation", "IPCC Models", "Ensemble Forecasting",
        "Ocean-Atmosphere Interaction", "Global Warming Scenarios", "Climate Feedbacks", "Coupled Climate Models", "Radiative Forcing"
    ],
    "Renewable Energy Systems": [
        "Solar PV Systems", "Wind Turbines", "Hydropower Technologies", "Bioenergy", "Geothermal Energy",
        "Smart Grids", "Energy Storage", "Inverter Technologies", "Grid Integration", "Off-Grid Systems",
        "Renewable Forecasting", "Energy Efficiency", "Distributed Energy", "Hybrid Systems", "Renewable Policy"
    ],
    "Carbon Accounting": [
        "GHG Inventory", "Carbon Footprint Tools", "Emission Factors", "Carbon Offsetting", "Scope 1/2/3 Emissions",
        "Carbon Neutral Strategies", "Sustainability Reporting", "Carbon Credits", "Cap-and-Trade", "Net Zero Goals",
        "Carbon Capture", "Carbon Audits", "ISO 14064", "LCA Emissions", "Emission Reduction Pathways"
    ],
    "Waste Management Tech": [
        "Waste Segregation", "Composting Systems", "Recycling Technologies", "E-Waste Processing", "Landfill Management",
        "Anaerobic Digestion", "Waste-to-Energy", "Hazardous Waste Handling", "Smart Bins", "Material Recovery Facilities",
        "Circular Economy Practices", "Zero Waste Design", "Plastic Alternatives", "Waste Auditing", "Sustainable Packaging"
    ],
    "Life Cycle Assessment": [
        "Goal & Scope Definition", "Inventory Analysis", "Impact Assessment", "Interpretation", "Cradle-to-Grave",
        "Cradle-to-Gate", "OpenLCA", "SimaPro", "Ecoinvent Database", "Carbon Hotspots",
        "Water Footprinting", "Energy Flow Mapping", "LCA of Products", "Environmental Indicators", "Functional Units"
    ],
    "Green Building Design": [
        "LEED Certification", "Passive Design", "Green Roofs", "Thermal Mass Optimization", "Daylighting Design",
        "HVAC Optimization", "Building Materials Analysis", "Energy Modeling", "BIM Integration", "Low-Carbon Materials",
        "Smart Lighting", "Indoor Air Quality", "Net Zero Energy", "Sustainable Site Planning", "Water Conservation"
    ],
    "Water Resource Management": [
        "Watershed Modeling", "Hydrological Analysis", "Water Quality Monitoring", "Water Footprint", "Irrigation Efficiency",
        "Stormwater Management", "Water-Energy Nexus", "Groundwater Recharge", "Water Policy", "Desalination",
        "Water Reuse", "Catchment Management", "Drought Management", "Hydraulic Modeling", "Integrated Water Management"
    ],
    "Smart Agriculture": [
        "Precision Farming", "IoT Sensors", "Automated Irrigation", "Crop Monitoring", "Drone Imaging",
        "Soil Moisture Sensing", "Yield Prediction", "Weather Data Analytics", "Sustainable Fertilization", "Farm Management Systems",
        "Agroecology", "Climate-Smart Agriculture", "Vertical Farming", "Hydroponics", "Sustainable Pest Control"
    ],
    "Environmental Policy": [
        "Regulatory Compliance", "Environmental Law", "Environmental Justice", "Climate Policy", "Environmental Impact Laws",
        "Public Policy Analysis", "Stakeholder Engagement", "Sustainability Governance", "International Agreements", "Policy Instruments",
        "Carbon Pricing", "Environmental Economics", "Environmental Diplomacy", "Environmental Litigation", "Policy Advocacy"
    ],
    "ESG Reporting": [
        "Sustainability Metrics", "GRI Standards", "SASB Framework", "Integrated Reporting", "ESG Risk Assessment",
        "Materiality Analysis", "ESG Scorecards", "Investor Disclosures", "Corporate Social Responsibility", "Sustainable Finance",
        "Impact Metrics", "Double Materiality", "Data Assurance", "Sustainable Supply Chains", "ESG Dashboards"
    ],
    "Impact Assessment": [
        "EIA Process", "Scoping & Screening", "Baseline Studies", "Impact Prediction", "Mitigation Measures",
        "Public Participation", "Cumulative Impact Assessment", "Post-Project Monitoring", "Social Impact Assessment", "Environmental Statements",
        "Regulatory Frameworks", "GIS Integration", "Biodiversity Impact", "Health Impact", "Strategic Environmental Assessment (SEA)"
    ],
    "Sustainable Development Goals": [
        "SDG Indicators", "SDG Reporting", "SDG Integration in Projects", "Cross-sectoral Analysis", "Data Collection for SDGs",
        "SDG Mapping", "National SDG Strategies", "Private Sector SDG Initiatives", "Localization of SDGs", "Education for SDGs",
        "Monitoring & Evaluation", "SDG Innovation", "Partnerships for the Goals", "Inclusive Development", "Global Benchmarks"
    ],
    "Remote Sensing": [
        "Satellite Imagery", "Spectral Analysis", "NDVI", "Landsat/ Sentinel Data", "Time-Series Monitoring",
        "Change Detection", "Land Cover Classification", "Atmospheric Corrections", "Thermal Sensing", "Remote Sensing Platforms",
        "Drone Mapping", "Hyperspectral Imaging", "SAR Data", "Object-Based Image Analysis", "Remote Sensing Software"
    ],
    "GIS for Environment": [
        "ArcGIS", "QGIS", "Geodatabase Design", "Spatial Analysis", "Map Visualization",
        "Raster/Vector Analysis", "Geoprocessing Tools", "Environmental Modeling", "Hotspot Mapping", "Web GIS",
        "Geostatistics", "Thematic Mapping", "Watershed Delineation", "Flood Mapping", "Habitat Suitability Analysis"
    ],
    "Environmental Monitoring": [
        "Air Quality Sensors", "Water Quality Probes", "Noise Pollution Monitoring", "IoT for Environment", "Satellite Data",
        "Mobile Sensing", "Citizen Science", "Real-Time Dashboards", "Environmental Indicators", "Monitoring Protocols",
        "Early Warning Systems", "Remote Sensing Integration", "Data Management Systems", "Environmental APIs", "Sensor Networks"
    ]
}


created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in env_sustainability_skills.items():
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
