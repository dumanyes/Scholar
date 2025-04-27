from projects.models import SkillsSubCategory, Skill
from django.db import IntegrityError

ml_skills = {
    "Supervised Learning": [
        "Linear Regression", "Logistic Regression", "Decision Trees", "Random Forest", "Support Vector Machines",
        "Naive Bayes", "Gradient Boosting", "KNN", "Classification", "Regression", "Scikit-learn Pipelines",
        "Model Validation", "Cross-Validation", "Training/Test Split", "Evaluation Metrics"
    ],
    "Unsupervised Learning": [
        "K-Means Clustering", "Hierarchical Clustering", "DBSCAN", "PCA", "Anomaly Detection",
        "Gaussian Mixture Models", "t-SNE", "Autoencoders", "Dimensionality Reduction", "Self-Organizing Maps",
        "Latent Variable Models", "Clustering Validation", "Topic Modeling", "Spectral Clustering", "Elbow Method"
    ],
    "Reinforcement Learning": [
        "Q-Learning", "SARSA", "Deep Q-Networks (DQN)", "Policy Gradient", "Actor-Critic",
        "Exploration Strategies", "Reward Shaping", "Markov Decision Processes", "Temporal Difference Learning",
        "Multi-Armed Bandits", "Value Iteration", "Monte Carlo Methods", "OpenAI Gym", "RLlib", "PPO"
    ],
    "Ensemble Methods": [
        "Bagging", "Boosting", "Random Forest", "AdaBoost", "Gradient Boosting Machines",
        "Voting Classifiers", "Stacking", "XGBoost", "LightGBM", "CatBoost", "Blending", "Out-of-Bag Error",
        "Feature Importance", "Bias-Variance Tradeoff", "Ensemble Diversity"
    ],
    "Feature Engineering": [
        "Feature Scaling", "Normalization", "Standardization", "One-Hot Encoding", "Label Encoding",
        "Feature Extraction", "Feature Selection", "Polynomial Features", "Missing Value Imputation",
        "Binning", "Encoding Categorical Variables", "Interaction Terms", "Log Transform", "Outlier Handling",
        "Skewness Correction"
    ],
    "Hyperparameter Tuning": [
        "Grid Search", "Random Search", "Bayesian Optimization", "Hyperopt", "Optuna", "CV in Tuning",
        "Tuning Tree Models", "Early Stopping", "Learning Rate Scheduling", "K-Fold with Tuning",
        "Validation Split", "SearchCV", "Automated Tuning", "Tuning Metrics", "Impact Analysis"
    ],
    "Anomaly Detection": [
        "Isolation Forest", "LOF", "Autoencoders for Anomaly", "One-Class SVM", "Z-Score Method",
        "Statistical Thresholding", "Time Series Anomaly", "Reconstruction Error", "Streaming Anomalies",
        "Anomaly Scores", "Multivariate Outliers", "Contextual Anomalies", "Visualizing Anomalies",
        "Real-World Anomalies", "Anomaly Metrics"
    ],
    "Model Evaluation": [
        "Confusion Matrix", "Accuracy", "Precision", "Recall", "F1 Score", "ROC Curve",
        "AUC", "PR Curve", "Log Loss", "Classification Report", "MSE", "R2", "Adjusted R2",
        "MAE", "MAPE"
    ],
    "Dimensionality Reduction": [
        "PCA", "t-SNE", "UMAP", "LDA", "Autoencoders", "SVD", "Factor Analysis",
        "Manifold Learning", "NMF", "Agglomeration", "Sparse PCA", "Kernel PCA", "Isomap",
        "Embedding", "Low-Dimensional Visualization"
    ],
    "Bayesian Models": [
        "Bayesian Inference", "Bayesian Linear Regression", "Bayesian Networks", "MCMC",
        "Gibbs Sampling", "Variational Inference", "Priors and Posteriors", "MAP Estimation",
        "Bayes Theorem", "Bayesian Optimization", "Bayesian Classification", "Probabilistic Programming",
        "PyMC3", "Stan", "Bayesian Logistic Regression"
    ],
    "ML Model Deployment": [
        "Model Serialization", "Pickle", "Joblib", "Flask APIs", "FastAPI", "Docker for ML",
        "Model Monitoring", "CI/CD for ML", "Realtime Inference", "Batch Predictions",
        "Streamlit", "TensorFlow Serving", "TorchServe", "MLflow", "ONNX"
    ],
    "Time Series Forecasting": [
        "ARIMA", "SARIMA", "Exponential Smoothing", "Prophet", "LSTM for Time Series", "Trend Analysis",
        "Seasonality", "Stationarity", "ACF", "PACF", "Lag Features", "Sliding Windows",
        "Multivariate Forecasting", "Time Series CV", "MAPE/RMSE"
    ],
    "Few-shot Learning": [
        "Siamese Networks", "Prototypical Networks", "Matching Networks", "Meta-learning", "Transfer Learning",
        "Low-Data Training", "Contrastive Learning", "Metric Learning", "One-shot Classification",
        "Zero-shot Learning", "Few-shot NLP", "Embedding Techniques", "Fine-tuning", "Data Augmentation",
        "Few-shot Benchmarks"
    ],
    "Meta Learning": [
        "MAML", "Reptile", "Gradient-Based Meta-Learning", "Learning-to-Learn", "Task Distribution",
        "Meta-Testing", "Meta-Training", "Fast Adaptation", "Meta-SGD", "Meta RL",
        "Transferable Representations", "Learned Optimizers", "Meta Datasets", "NAS", "Meta-Loss Functions"
    ],
    "AutoML": [
        "AutoKeras", "TPOT", "Auto-sklearn", "H2O AutoML", "Google AutoML", "Search Space Design",
        "Hyperparameter Search", "Pipeline Automation", "Low-Code ML", "Time Budgeting",
        "Model Selection", "Preprocessing Automation", "MLflow Integration", "Explainability in AutoML",
        "AutoML Comparison"
    ]
}

created = 0
skipped = 0
missing_subcats = []

for subcat_name, skill_list in ml_skills.items():
    try:
        subcat = SkillsSubCategory.objects.get(name=subcat_name)
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
    except SkillsSubCategory.DoesNotExist:
        missing_subcats.append(subcat_name)
        print(f"❌ Subcategory not found: {subcat_name}")

print("\n🎉 Import Complete!")
print(f"✅ Total created: {created}")
print(f"⚠️ Total skipped: {skipped}")
if missing_subcats:
    print("❌ Missing subcategories:")
    for subcat in missing_subcats:
        print(f" - {subcat}")
