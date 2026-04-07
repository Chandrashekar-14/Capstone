import pandas as pd
from sklearn.linear_model import LogisticRegression
from .models import Student

def train_model():
    # Get all students
    students = Student.objects.all()

    data = []
    for s in students:
        # Normalize fields to 0-100 scale
        data.append([
            s.cgpa * 10,
            s.skills * 10,
            s.academics * 10,
            s.practice * 10,
            s.projects * 10,
            s.aptitude * 5,
            int(s.placed)
        ])

    df = pd.DataFrame(data, columns=[
        'cgpa','skills','academics','practice','projects','aptitude','placed'
    ])

    X = df[['cgpa','skills','academics','practice','projects','aptitude']]
    y = df['placed']

    # Train logistic regression model
    model = LogisticRegression()
    model.fit(X, y)

    return model

def predict_student(student, model):
    features = [[
        student.cgpa * 10,
        student.skills * 10,
        student.academics * 10,
        student.practice * 10,
        student.projects * 10,
        student.aptitude * 5
    ]]

    result = model.predict(features)[0]
    prob = model.predict_proba(features)[0][1] * 100  # probability of placement

    return {
        'status': "Placement Ready ✅" if result == 1 else "Not Ready ❌",
        'score': round(prob, 2)
    }