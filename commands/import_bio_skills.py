from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

bioinformatics_skills = {
    "Sequence Alignment": [
        "Pairwise Alignment", "Multiple Sequence Alignment", "BLAST", "ClustalW", "MAFFT", "T-Coffee",
        "Smith-Waterman Algorithm", "Needleman-Wunsch Algorithm", "Scoring Matrices", "Gap Penalties",
        "Global vs Local Alignment", "DNA Alignment", "Protein Sequence Alignment", "FASTA Format", "Sequence Homology"
    ],
    "Gene Expression Analysis": [
        "Microarray Analysis", "RNA-seq", "qPCR", "Normalization Methods", "Differential Expression", "Gene Ontology",
        "FPKM/TPM", "DESeq2", "edgeR", "Heatmaps", "Volcano Plots", "Clustering Expression Data", "Batch Effect Correction",
        "Bioconductor", "Expression Profiling"
    ],
    "Genome Annotation": [
        "Gene Prediction", "Ab Initio Annotation", "Functional Annotation", "Promoter Identification", "Repeat Masking",
        "Genome Browsers", "Ensembl", "UCSC Genome Browser", "Annotation Tools", "Gene Ontology Mapping", "GFF/GTF Formats",
        "BLASTx", "Transcript Assembly", "ORF Prediction", "Annotation Pipelines"
    ],
    "BLAST Tools": [
        "BLASTn", "BLASTp", "BLASTx", "PSI-BLAST", "MEGABLAST", "Sequence Alignment", "Database Searching", "Query Coverage",
        "Percent Identity", "E-values", "Bit Score", "NCBI BLAST", "Command Line BLAST", "Remote BLAST", "BLAST Output Parsing"
    ],
    "RNA-Seq": [
        "Transcript Quantification", "Alignment Tools", "STAR Aligner", "HISAT2", "Transcriptome Assembly", "DESeq2",
        "edgeR", "Splice Variant Detection", "Expression Normalization", "Count Matrices", "RSeQC", "FastQC", "FeatureCounts",
        "Gene Fusion Detection", "Quality Trimming"
    ],
    "Protein Structure Prediction": [
        "Homology Modeling", "Fold Recognition", "Ab Initio Modeling", "Secondary Structure Prediction", "AlphaFold",
        "Ramachandran Plots", "PDB Database", "Structural Alignment", "Energy Minimization", "Threading", "Tertiary Structure",
        "Domain Prediction", "Template Selection", "3D Visualization", "Protein Modeling Tools"
    ],
    "Molecular Docking": [
        "Ligand Preparation", "Protein Preparation", "Binding Affinity", "Scoring Functions", "Docking Tools", "AutoDock",
        "PyMOL Integration", "Binding Site Prediction", "Flexible Docking", "Rigid Docking", "Molecular Dynamics", "Virtual Screening",
        "Grid Generation", "Docking Validation", "Visualization of Complexes"
    ],
    "Systems Biology": [
        "Pathway Analysis", "Network Biology", "Gene Regulatory Networks", "Protein Interaction Networks", "Metabolic Modeling",
        "Cytoscape", "Simulation Models", "Boolean Networks", "ODE Models", "SBML", "Flux Balance Analysis", "Time Series Analysis",
        "Data Integration", "Omics Integration", "Model Validation"
    ],
    "Biological Databases": [
        "GenBank", "Ensembl", "UCSC", "KEGG", "PDB", "UniProt", "GEO", "ArrayExpress", "Pfam", "InterPro", "dbSNP", "OMIM",
        "BioMart", "DDBJ", "BRENDA"
    ],
    "Biostatistics": [
        "Descriptive Statistics", "T-tests", "Chi-Square Tests", "ANOVA", "Correlation Coefficients", "Linear Regression",
        "Logistic Regression", "Survival Analysis", "Kaplan-Meier Curves", "Hazard Ratios", "P-values", "Confidence Intervals",
        "Multivariate Analysis", "Bayesian Methods", "Biostatistical Software"
    ],
    "Clinical Bioinformatics": [
        "EHR Data Mining", "Clinical Trials Analysis", "Disease Biomarkers", "Pharmacogenomics", "Precision Medicine",
        "GWAS", "ICD Codes", "HL7 Standards", "Variant Annotation", "Clinical Decision Support", "FHIR", "Genotype-Phenotype Links",
        "Therapeutic Targeting", "Clinical Database Integration", "Data Harmonization"
    ],
    "Genomic Variant Calling": [
        "SNP Calling", "Indel Detection", "GATK", "FreeBayes", "SAMtools", "VCF Format", "Quality Filtering", "Base Recalibration",
        "Variant Annotation", "Structural Variant Detection", "Read Mapping", "Alignment QC", "BAM File Processing",
        "Genotyping", "Comparison to dbSNP"
    ],
    "Transcriptomics": [
        "Transcript Assembly", "Expression Quantification", "Alternative Splicing", "Isoform Detection", "Transcript Isoforms",
        "Normalization Techniques", "Differential Transcript Usage", "RNA Editing", "Time-Series Expression", "Single-cell Transcriptomics",
        "Transcriptome Browsers", "Tuxedo Suite", "Expression Heatmaps", "Gene Fusion Analysis", "Comparative Transcriptomics"
    ],
    "Epigenomics": [
        "DNA Methylation", "Histone Modification", "ChIP-seq", "ATAC-seq", "Bisulfite Sequencing", "Chromatin Accessibility",
        "Epigenetic Marks", "Chromatin Immunoprecipitation", "Peak Calling", "Genome-wide Profiling", "Epigenome Browsers",
        "Differential Methylation", "Histone Code", "Nucleosome Positioning", "Enhancer Mapping"
    ],
    "Microbiome Analysis": [
        "16S rRNA Analysis", "Shotgun Metagenomics", "QIIME2", "Microbial Diversity", "Alpha/Beta Diversity", "Taxonomic Classification",
        "OTUs", "ASVs", "Phylogenetic Trees", "Functional Prediction", "LEfSe", "Rarefaction", "Contaminant Filtering",
        "Metagenomic Assembly", "Host-Microbiome Interaction"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in bioinformatics_skills.items():
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
