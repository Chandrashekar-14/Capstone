import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from .models import Student
from .scoring import calculate_readiness_score, ROLE_WEIGHTS


def train_model():
    students = Student.objects.all()

    data = []
    for s in students:
        data.append({
            'skills': s.skills,
            'academics': s.academics,
            'practice': s.practice,
            'projects': s.projects,
            'aptitude': s.aptitude,
            'placed': 1 if s.placed else 0
        })

    df = pd.DataFrame(data)

    # 🚨 safety check
    if df.empty or len(df) < 5:
        return None

    X = df[['skills','academics','practice','projects','aptitude']]
    y = df['placed']

    model = RandomForestClassifier(n_estimators=100)
    model.fit(X, y)

    return model


def analyze_student(student, model, target_role=None):
    input_data = [[
        student.skills,
        student.academics,
        student.practice,
        student.projects,
        student.aptitude
    ]]

    # 🚨 if model not trained
    if model is None:
        probability = 0
        prediction = "Insufficient Data"
    else:
        prediction = model.predict(input_data)[0]
        probability = model.predict_proba(input_data)[0][1] * 100
        prediction = "Placed" if prediction == 1 else "Not Likely"

    features = ['Skills','Academics','Practice','Projects','Aptitude']

    # Use role-specific thresholds for weak/strong areas
    weights = ROLE_WEIGHTS.get(target_role, {'skills': 0.25, 'academics': 0.20, 'practice': 0.20, 'projects': 0.20, 'aptitude': 0.15})

    # Calculate weighted thresholds based on role importance
    thresholds = {}
    for i, feature in enumerate(['skills', 'academics', 'practice', 'projects', 'aptitude']):
        # Higher weight = lower threshold for "weak" (more important to improve)
        base_threshold = 70  # Default threshold
        weight_adjustment = (1 - weights[feature]) * 20  # 0-20 point adjustment
        thresholds[features[i]] = base_threshold - weight_adjustment

    weak_areas = []
    strong_areas = []

    for i in range(len(features)):
        threshold = thresholds[features[i]]
        if input_data[0][i] < threshold:
            weak_areas.append(features[i])
        else:
            strong_areas.append(features[i])

    return {
        "prediction": prediction,
        "probability": round(probability,2),
        "weak_areas": weak_areas,
        "strong_areas": strong_areas
    }