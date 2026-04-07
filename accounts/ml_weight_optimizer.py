"""
ML Weight Optimizer - Automatically learns optimal weights from real placement data
Uses multiple ensemble models to determine feature importance based on actual placement outcomes
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
from .models import Student
import json

class WeightOptimizer:
    """
    Learns optimal weights for readiness score based on:
    - Feature importance from multiple ML models
    - Real placement outcomes
    - Cross-validation for reliability
    """
    
    def __init__(self):
        self.trained_models = {}
        self.feature_importance = {}
        self.model_performance = {}
        self.optimal_weights = {}
        self.data = None
        self.X_scaled = None
        self.y = None
        
    def prepare_data(self):
        """
        Prepare training data from student database
        Features: skills, academics, practice, projects, aptitude
        Target: placement (binary: placed or not)
        """
        students = Student.objects.all()
        
        if not students.exists():
            raise ValueError("No student data found in database")
        
        data = []
        for s in students:
            data.append({
                'skills': s.skills,
                'academics': s.academics,
                'practice': s.practice,
                'projects': s.projects,
                'aptitude': s.aptitude,
                'cgpa': s.cgpa,
                'placed': int(s.placed)
            })
        
        self.data = pd.DataFrame(data)
        
        # Separate features and target
        self.X = self.data[['skills', 'academics', 'practice', 'projects', 'aptitude']]
        self.y = self.data['placed']
        
        # Standardize features for better model training
        scaler = StandardScaler()
        self.X_scaled = scaler.fit_transform(self.X)
        
        return self.X, self.y
    
    def train_models(self):
        """
        Train multiple models to get robust feature importance estimates
        Uses ensemble methods which are more reliable than single models
        """
        if self.X_scaled is None:
            self.prepare_data()
        
        models = {
            'Logistic Regression': LogisticRegression(max_iter=1000, random_state=42),
            'Random Forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
            'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
        }
        
        for name, model in models.items():
            try:
                # Train model
                model.fit(self.X_scaled, self.y)
                self.trained_models[name] = model
                
                # Calculate cross-validation score
                cv_score = cross_val_score(model, self.X_scaled, self.y, cv=5, scoring='roc_auc')
                
                # Get predictions for performance metrics
                y_pred = model.predict(self.X_scaled)
                y_proba = model.predict_proba(self.X_scaled)[:, 1]
                roc_score = roc_auc_score(self.y, y_proba)
                
                self.model_performance[name] = {
                    'cv_mean': float(cv_score.mean()),
                    'cv_std': float(cv_score.std()),
                    'roc_auc': float(roc_score)
                }
                
                # Get feature importance
                if hasattr(model, 'coef_'):
                    # For linear models, normalize coefficients
                    importance = np.abs(model.coef_[0])
                    importance = importance / importance.sum()
                elif hasattr(model, 'feature_importances_'):
                    # For tree-based models
                    importance = model.feature_importances_
                else:
                    importance = np.ones(5) / 5
                
                self.feature_importance[name] = {
                    'skills': float(importance[0]),
                    'academics': float(importance[1]),
                    'practice': float(importance[2]),
                    'projects': float(importance[3]),
                    'aptitude': float(importance[4])
                }
                
            except Exception as e:
                print(f"Error training {name}: {str(e)}")
        
        return self.feature_importance, self.model_performance
    
    def calculate_optimal_weights(self):
        """
        Combine feature importance from all models using weighted average
        Prioritizes Random Forest and Gradient Boosting (ensemble methods)
        """
        if not self.feature_importance:
            self.train_models()
        
        # Weights for combining models: Trust ensemble methods more
        model_weights = {
            'Random Forest': 0.45,
            'Gradient Boosting': 0.45,
            'Logistic Regression': 0.10
        }
        
        features = ['skills', 'academics', 'practice', 'projects', 'aptitude']
        averaged_importance = {feat: 0 for feat in features}
        
        for model_name, importance in self.feature_importance.items():
            weight = model_weights.get(model_name, 0)
            for feat in features:
                averaged_importance[feat] += importance[feat] * weight
        
        # Normalize to sum to 1.0
        total = sum(averaged_importance.values())
        self.optimal_weights = {k: v/total for k, v in averaged_importance.items()}
        
        return self.optimal_weights
    
    def get_insights(self):
        """
        Generate actionable insights from the trained models
        """
        if not self.optimal_weights:
            self.calculate_optimal_weights()
        
        insights = {
            'total_students': len(self.data),
            'placed_students': int(self.y.sum()),
            'placement_rate': float(self.y.sum() / len(self.y) * 100),
            'optimal_weights': self.optimal_weights,
            'feature_importance': self.feature_importance,
            'model_performance': self.model_performance,
            'top_factor': max(self.optimal_weights.items(), key=lambda x: x[1])[0],
            'top_factor_weight': max(self.optimal_weights.values())
        }
        
        return insights
    
    def save_weights_to_db(self):
        """
        Save optimized weights to database for persistence
        Creates or updates a WeightConfiguration record
        """
        from django.core.cache import cache
        import json
        
        if not self.optimal_weights:
            self.calculate_optimal_weights()
        
        # Save to cache (can be extended to database model)
        cache.set('optimal_weights', self.optimal_weights, timeout=None)
        
        return self.optimal_weights


def get_optimal_weights():
    """
    Retrieve saved optimal weights from cache
    Falls back to default weights if not trained
    """
    from django.core.cache import cache
    
    weights = cache.get('optimal_weights')
    
    if weights is None:
        # Default weights if no training done yet
        weights = {
            'skills': 0.25,
            'academics': 0.20,
            'practice': 0.20,
            'projects': 0.20,
            'aptitude': 0.15
        }
    
    return weights


def retrain_weights():
    """
    Main function to trigger weight retraining
    """
    optimizer = WeightOptimizer()
    
    try:
        # Prepare data
        optimizer.prepare_data()
        
        # Train models
        optimizer.train_models()
        
        # Calculate optimal weights
        optimal_weights = optimizer.calculate_optimal_weights()
        
        # Get insights
        insights = optimizer.get_insights()
        
        # Save weights
        optimizer.save_weights_to_db()
        
        return {
            'success': True,
            'message': 'Weights retraining completed successfully',
            'insights': insights
        }
    
    except Exception as e:
        return {
            'success': False,
            'message': f'Error during retraining: {str(e)}',
            'insights': None
        }
