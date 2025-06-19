
import json
import pickle
import os
from datetime import datetime
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.multioutput import MultiOutputClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer
from sklearn.metrics import classification_report, accuracy_score
import numpy as np
import logging

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_FILE = os.path.join(BASE_DIR, 'memory.json')
MODEL_DIR = os.path.join(BASE_DIR, 'models')

class MemoryPredictor:
    def __init__(self):
        self.text_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.type_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        self.tag_binarizer = MultiLabelBinarizer()
        
        # Models
        self.type_model = LogisticRegression(random_state=42)
        self.category_model = LogisticRegression(random_state=42)
        self.tag_model = MultinomialNB()
        self.score_model = LogisticRegression(random_state=42)
        
        self.is_trained = False
        
    def load_training_data(self):
        """Load and prepare training data from memory.json"""
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
            
            if len(memory) < 10:
                print("⚠️  Need at least 10 memory entries for training")
                return None, None, None, None, None
            
            # Prepare features and labels
            texts = []
            types = []
            categories = []
            tags = []
            scores = []
            
            for entry in memory:
                # Combine input, output, and topic for text features
                text_content = f"{entry.get('input', '')} {entry.get('output', '')} {entry.get('topic', '')}"
                texts.append(text_content)
                
                # Labels
                types.append(entry.get('type', 'Unknown'))
                categories.append(entry.get('category', 'unknown'))
                tags.append(entry.get('tags', []))
                
                # Normalize scores to ranges (0-25 scale)
                score = entry.get('score', 0)
                max_score = entry.get('maxScore', 25)
                normalized_score = min(score, max_score)  # Cap at max
                score_range = self._score_to_range(normalized_score, max_score)
                scores.append(score_range)
            
            print(f"📊 Loaded {len(texts)} training samples")
            return texts, types, categories, tags, scores
            
        except Exception as e:
            print(f"❌ Error loading training data: {e}")
            return None, None, None, None, None
    
    def _score_to_range(self, score, max_score):
        """Convert numeric score to categorical range"""
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        if percentage >= 90:
            return "excellent"
        elif percentage >= 75:
            return "high"
        elif percentage >= 50:
            return "medium"
        elif percentage >= 25:
            return "low"
        else:
            return "minimal"
    
    def train_models(self):
        """Train all prediction models"""
        print("🧠 Training memory prediction models...")
        
        texts, types, categories, tags, scores = self.load_training_data()
        if texts is None:
            return False
        
        try:
            # Prepare text features
            X = self.text_vectorizer.fit_transform(texts)
            
            # Prepare labels
            y_type = self.type_encoder.fit_transform(types)
            y_category = self.category_encoder.fit_transform(categories)
            y_tags = self.tag_binarizer.fit_transform(tags)
            y_score = LabelEncoder().fit_transform(scores)
            
            # Train models
            print("📈 Training type predictor...")
            self.type_model.fit(X, y_type)
            
            print("📈 Training category predictor...")
            self.category_model.fit(X, y_category)
            
            print("📈 Training tag predictor...")
            self.tag_model.fit(X, y_tags)
            
            print("📈 Training score predictor...")
            self.score_model.fit(X, y_score)
            
            # Evaluate models
            self._evaluate_models(X, y_type, y_category, y_tags, y_score)
            
            self.is_trained = True
            self.save_models()
            
            print("✅ Model training complete!")
            return True
            
        except Exception as e:
            print(f"❌ Error training models: {e}")
            return False
    
    def _evaluate_models(self, X, y_type, y_category, y_tags, y_score):
        """Evaluate model performance"""
        if len(set(y_type)) > 1:
            X_train, X_test, y_type_train, y_type_test = train_test_split(X, y_type, test_size=0.2, random_state=42)
            type_pred = self.type_model.predict(X_test)
            print(f"📊 Type prediction accuracy: {accuracy_score(y_type_test, type_pred):.2f}")
        
        if len(set(y_category)) > 1:
            X_train, X_test, y_cat_train, y_cat_test = train_test_split(X, y_category, test_size=0.2, random_state=42)
            cat_pred = self.category_model.predict(X_test)
            print(f"📊 Category prediction accuracy: {accuracy_score(y_cat_test, cat_pred):.2f}")
    
    def predict(self, input_text, output_text="", topic=""):
        """Predict type, category, tags, and score for new text"""
        if not self.is_trained:
            if not self.load_models():
                return self._fallback_prediction(input_text, output_text, topic)
        
        try:
            # Prepare text
            text_content = f"{input_text} {output_text} {topic}"
            X = self.text_vectorizer.transform([text_content])
            
            # Predictions
            type_pred = self.type_encoder.inverse_transform(self.type_model.predict(X))[0]
            category_pred = self.category_encoder.inverse_transform(self.category_model.predict(X))[0]
            
            # Tag prediction (get top 3 most likely tags)
            tag_probs = self.tag_model.predict_proba(X)[0]
            top_tag_indices = np.argsort(tag_probs)[-3:]  # Top 3
            predicted_tags = []
            for idx in top_tag_indices:
                if tag_probs[idx] > 0.3:  # Confidence threshold
                    tag_labels = self.tag_binarizer.classes_
                    if idx < len(tag_labels):
                        predicted_tags.append(tag_labels[idx])
            
            # Score prediction
            score_range = self.score_model.predict(X)[0]
            score_map = {"minimal": 5, "low": 10, "medium": 15, "high": 20, "excellent": 25}
            predicted_score = score_map.get(score_range, 15)
            
            return {
                "type": type_pred,
                "category": category_pred,
                "tags": predicted_tags,
                "score": predicted_score,
                "confidence": {
                    "type": float(np.max(self.type_model.predict_proba(X))),
                    "category": float(np.max(self.category_model.predict_proba(X))),
                    "score_range": score_range
                }
            }
            
        except Exception as e:
            print(f"⚠️  Prediction error: {e}")
            return self._fallback_prediction(input_text, output_text, topic)
    
    def _fallback_prediction(self, input_text, output_text, topic):
        """Fallback prediction using simple heuristics"""
        text = f"{input_text} {output_text} {topic}".lower()
        
        # Simple type detection
        if any(word in text for word in ['bug', 'fix', 'error', 'issue']):
            pred_type = "BugFix"
        elif any(word in text for word in ['test', 'testing', 'verify']):
            pred_type = "SystemTest"
        elif any(word in text for word in ['decision', 'choose', 'decide']):
            pred_type = "Decision"
        elif any(word in text for word in ['build', 'implement', 'feature']):
            pred_type = "BuildLog"
        else:
            pred_type = "General"
        
        # Simple category detection
        if any(word in text for word in ['system', 'api', 'endpoint']):
            pred_category = "system"
        elif any(word in text for word in ['test', 'testing']):
            pred_category = "test"
        elif any(word in text for word in ['integration', 'connect']):
            pred_category = "integration"
        else:
            pred_category = "general"
        
        # Simple tags
        pred_tags = []
        tag_keywords = ['api', 'test', 'fix', 'feature', 'system', 'integration']
        for keyword in tag_keywords:
            if keyword in text:
                pred_tags.append(keyword)
        
        return {
            "type": pred_type,
            "category": pred_category,
            "tags": pred_tags[:3],
            "score": 15,
            "confidence": {"type": 0.5, "category": 0.5, "score_range": "medium"}
        }
    
    def save_models(self):
        """Save trained models to disk"""
        os.makedirs(MODEL_DIR, exist_ok=True)
        
        model_data = {
            'text_vectorizer': self.text_vectorizer,
            'type_encoder': self.type_encoder,
            'category_encoder': self.category_encoder,
            'tag_binarizer': self.tag_binarizer,
            'type_model': self.type_model,
            'category_model': self.category_model,
            'tag_model': self.tag_model,
            'score_model': self.score_model,
            'trained_at': datetime.now().isoformat(),
            'is_trained': True
        }
        
        model_file = os.path.join(MODEL_DIR, 'memory_predictor.pkl')
        with open(model_file, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"💾 Models saved to {model_file}")
    
    def load_models(self):
        """Load trained models from disk"""
        model_file = os.path.join(MODEL_DIR, 'memory_predictor.pkl')
        
        try:
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            self.text_vectorizer = model_data['text_vectorizer']
            self.type_encoder = model_data['type_encoder']
            self.category_encoder = model_data['category_encoder']
            self.tag_binarizer = model_data['tag_binarizer']
            self.type_model = model_data['type_model']
            self.category_model = model_data['category_model']
            self.tag_model = model_data['tag_model']
            self.score_model = model_data['score_model']
            self.is_trained = model_data.get('is_trained', False)
            
            print(f"📦 Models loaded from {model_file}")
            print(f"   Trained at: {model_data.get('trained_at', 'Unknown')}")
            return True
            
        except (FileNotFoundError, pickle.PickleError) as e:
            print(f"⚠️  Could not load models: {e}")
            return False
    
    def retrain_if_needed(self, min_new_entries=5):
        """Retrain models if there are enough new entries since last training"""
        try:
            model_file = os.path.join(MODEL_DIR, 'memory_predictor.pkl')
            
            if not os.path.exists(model_file):
                print("🔄 No existing model found, training new model...")
                return self.train_models()
            
            # Check if we have enough new data since last training
            with open(MEMORY_FILE, 'r') as f:
                memory = json.load(f)
            
            # Load last training timestamp
            try:
                with open(model_file, 'rb') as f:
                    model_data = pickle.load(f)
                last_trained = datetime.fromisoformat(model_data.get('trained_at', '2000-01-01'))
            except:
                last_trained = datetime(2000, 1, 1)
            
            # Count new entries since last training
            new_entries = 0
            for entry in memory:
                try:
                    entry_time = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
                    if entry_time.replace(tzinfo=None) > last_trained:
                        new_entries += 1
                except:
                    continue
            
            if new_entries >= min_new_entries:
                print(f"🔄 Found {new_entries} new entries, retraining models...")
                return self.train_models()
            else:
                print(f"📊 Only {new_entries} new entries, using existing model")
                return self.load_models()
                
        except Exception as e:
            print(f"❌ Error checking retrain status: {e}")
            return False

def main():
    """Train models with current memory data"""
    predictor = MemoryPredictor()
    
    # Check if retraining is needed
    success = predictor.retrain_if_needed()
    
    if success:
        print("✅ Memory prediction system ready!")
        
        # Test prediction
        test_prediction = predictor.predict(
            "Testing the new auto-logging system with intelligent filtering",
            "System successfully filtered low-importance events and tagged appropriately"
        )
        print(f"🧪 Test prediction: {test_prediction}")
    else:
        print("❌ Failed to prepare prediction system")

if __name__ == "__main__":
    main()
