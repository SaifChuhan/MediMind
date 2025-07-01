import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Define tokenizer function to replace lambda
def symptom_tokenizer(text):
    return [s.strip() for s in text.split(",")]

# Create directory for models if it doesn't exist
MODEL_DIR = "medicine_model"
if not os.path.exists(MODEL_DIR):
    os.makedirs(MODEL_DIR)

# 1. Generate Synthetic Dataset for Disease Prediction
np.random.seed(42)
symptoms_list = [
    "fever", "cough", "sore_throat", "fatigue", "headache", "nausea", "vomiting",
    "diarrhea", "shortness_of_breath", "chest_pain", "rash", "joint_pain",
    "muscle_pain", "dizziness", "high_blood_sugar", "increased_thirst",
    "frequent_urination", "blurred_vision", "weight_loss", "abdominal_pain"
]

diseases = [
    "Common Cold", "Flu", "COVID-19", "Diabetes", "Hypertension", "Asthma",
    "Migraine", "Gastroenteritis", "Arthritis", "Pneumonia"
]

# Generate synthetic symptom-disease data
n_samples = 1000
data = {
    "symptoms": [],
    "disease": []
}

for _ in range(n_samples):
    disease = np.random.choice(diseases)
    n_symptoms = np.random.randint(2, 6)
    selected_symptoms = np.random.choice(symptoms_list, n_symptoms, replace=False)
    symptoms_str = ", ".join(selected_symptoms)
    data["symptoms"].append(symptoms_str)
    data["disease"].append(disease)

df_disease = pd.DataFrame(data)

# Disease-specific symptom tendencies
disease_symptom_map = {
    "Common Cold": ["cough", "sore_throat", "fever"],
    "Flu": ["fever", "fatigue", "muscle_pain", "headache"],
    "COVID-19": ["fever", "cough", "shortness_of_breath", "fatigue"],
    "Diabetes": ["high_blood_sugar", "increased_thirst", "frequent_urination"],
    "Hypertension": ["headache", "dizziness", "chest_pain"],
    "Asthma": ["shortness_of_breath", "chest_pain"],
    "Migraine": ["headache", "nausea", "dizziness"],
    "Gastroenteritis": ["nausea", "vomiting", "diarrhea"],
    "Arthritis": ["joint_pain", "muscle_pain"],
    "Pneumonia": ["fever", "cough", "shortness_of_breath", "chest_pain"]
}

# Adjust dataset to reflect disease-specific symptoms
for idx, row in df_disease.iterrows():
    disease = row["disease"]
    if np.random.random() < 0.7:  # 70% chance to include specific symptoms
        specific_symptoms = disease_symptom_map[disease]
        other_symptoms = np.random.choice(
            [s for s in symptoms_list if s not in specific_symptoms],
            np.random.randint(0, 3)
        )
        all_symptoms = list(set(specific_symptoms + list(other_symptoms)))
        df_disease.at[idx, "symptoms"] = ", ".join(all_symptoms)

# 2. Train Disease Prediction Model
# Convert symptoms to feature vectors
vectorizer = CountVectorizer(tokenizer=symptom_tokenizer)
X_disease = vectorizer.fit_transform(df_disease["symptoms"])
y_disease = df_disease["disease"]

# Split data
X_train_d, X_test_d, y_train_d, y_test_d = train_test_split(
    X_disease, y_disease, test_size=0.2, random_state=42
)

# Train Random Forest for disease prediction
disease_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
disease_predictor.fit(X_train_d, y_train_d)

# Evaluate
y_pred_d = disease_predictor.predict(X_test_d)
print(f"Disease Prediction Accuracy: {accuracy_score(y_test_d, y_pred_d):.2f}")

# Save disease prediction model and vectorizer
joblib.dump(disease_predictor, os.path.join(MODEL_DIR, "disease_predictor.pkl"))
joblib.dump(vectorizer, os.path.join(MODEL_DIR, "symptom_encoder.pkl"))

# 3. Generate Synthetic Dataset for Medicine Category Prediction
categories = ["Oral", "Injection", "Topical", "Inhaler", "Other"]
medicine_data = {
    "age": [],
    "is_diabetic": [],
    "has_hypertension": [],
    "disease_encoded": [],
    "category": []
}

disease_encoder = LabelEncoder()
disease_encoded = disease_encoder.fit_transform(df_disease["disease"])

for idx, disease in enumerate(df_disease["disease"]):
    age = np.random.randint(18, 90)
    is_diabetic = 1 if disease == "Diabetes" or np.random.random() < 0.2 else 0
    has_hypertension = 1 if disease == "Hypertension" or np.random.random() < 0.2 else 0
    disease_idx = disease_encoded[idx]
    
    # Assign category based on disease
    if disease == "Asthma":
        category = "Inhaler"
    elif disease in ["Diabetes", "Hypertension"]:
        category = np.random.choice(["Oral", "Injection"], p=[0.7, 0.3])
    elif disease == "Arthritis":
        category = np.random.choice(["Oral", "Topical"], p=[0.6, 0.4])
    else:
        category = np.random.choice(categories, p=[0.5, 0.2, 0.1, 0.1, 0.1])
    
    medicine_data["age"].append(age)
    medicine_data["is_diabetic"].append(is_diabetic)
    medicine_data["has_hypertension"].append(has_hypertension)
    medicine_data["disease_encoded"].append(disease_idx)
    medicine_data["category"].append(category)

df_medicine = pd.DataFrame(medicine_data)

# 4. Train Medicine Category Prediction Model
category_encoder = LabelEncoder()
y_category = category_encoder.fit_transform(df_medicine["category"])
X_medicine = df_medicine[["age", "is_diabetic", "has_hypertension", "disease_encoded"]]

# Split data
X_train_m, X_test_m, y_train_m, y_test_m = train_test_split(
    X_medicine, y_category, test_size=0.2, random_state=42
)

# Train Random Forest for category prediction
medicine_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
medicine_predictor.fit(X_train_m, y_train_m)

# Evaluate
y_pred_m = medicine_predictor.predict(X_test_m)
print(f"Medicine Category Prediction Accuracy: {accuracy_score(y_test_m, y_pred_m):.2f}")

# Save medicine prediction model and encoders
joblib.dump(medicine_predictor, os.path.join(MODEL_DIR, "medicine_predictor.pkl"))
joblib.dump(disease_encoder, os.path.join(MODEL_DIR, "disease_encoder.pkl"))
joblib.dump(category_encoder, os.path.join(MODEL_DIR, "category_encoder.pkl"))

print(f"Models and encoders saved to {MODEL_DIR}/")