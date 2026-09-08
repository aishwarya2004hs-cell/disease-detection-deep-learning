"""
Database utilities for disease detection project.
"""

import sqlite3
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DiseaseDatabase:
    """
    SQLite database for storing predictions and patient data.
    """

    def __init__(self, db_path='database/disease_detection.db'):
        """
        Initialize database connection.

        Args:
            db_path (str): Path to database file
        """
        self.db_path = db_path
        self.connection = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Connect to database."""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.cursor = self.connection.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")

    def create_tables(self):
        """Create database tables."""
        tables = [
            """
            CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                gender TEXT,
                contact TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS medical_images (
                image_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                image_type TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS predictions (
                prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                patient_id INTEGER NOT NULL,
                model_name TEXT,
                predicted_class TEXT,
                confidence REAL,
                predictions_json TEXT,
                prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES medical_images(image_id),
                FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS model_performance (
                performance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT,
                accuracy REAL,
                precision REAL,
                recall REAL,
                f1_score REAL,
                test_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        ]

        for table in tables:
            try:
                self.cursor.execute(table)
                self.connection.commit()
            except sqlite3.Error as e:
                logger.error(f"Error creating table: {e}")

        logger.info("Database tables created successfully")

    def add_patient(self, name, age=None, gender=None, contact=None):
        """
        Add patient to database.

        Args:
            name (str): Patient name
            age (int): Patient age
            gender (str): Patient gender
            contact (str): Patient contact

        Returns:
            int: Patient ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO patients (name, age, gender, contact)
                VALUES (?, ?, ?, ?)
            """, (name, age, gender, contact))
            self.connection.commit()
            patient_id = self.cursor.lastrowid
            logger.info(f"Patient added with ID: {patient_id}")
            return patient_id
        except sqlite3.Error as e:
            logger.error(f"Error adding patient: {e}")
            return None

    def add_medical_image(self, patient_id, image_path, image_type):
        """
        Add medical image to database.

        Args:
            patient_id (int): Patient ID
            image_path (str): Path to image
            image_type (str): Type of image (e.g., X-ray, MRI)

        Returns:
            int: Image ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO medical_images (patient_id, image_path, image_type)
                VALUES (?, ?, ?)
            """, (patient_id, image_path, image_type))
            self.connection.commit()
            image_id = self.cursor.lastrowid
            logger.info(f"Image added with ID: {image_id}")
            return image_id
        except sqlite3.Error as e:
            logger.error(f"Error adding image: {e}")
            return None

    def add_prediction(self, image_id, patient_id, model_name, predicted_class, 
                      confidence, predictions_dict):
        """
        Add prediction to database.

        Args:
            image_id (int): Image ID
            patient_id (int): Patient ID
            model_name (str): Model name
            predicted_class (str): Predicted disease class
            confidence (float): Confidence score
            predictions_dict (dict): All predictions dictionary

        Returns:
            int: Prediction ID
        """
        try:
            predictions_json = json.dumps(predictions_dict)
            self.cursor.execute("""
                INSERT INTO predictions 
                (image_id, patient_id, model_name, predicted_class, confidence, predictions_json)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (image_id, patient_id, model_name, predicted_class, confidence, predictions_json))
            self.connection.commit()
            prediction_id = self.cursor.lastrowid
            logger.info(f"Prediction added with ID: {prediction_id}")
            return prediction_id
        except sqlite3.Error as e:
            logger.error(f"Error adding prediction: {e}")
            return None

    def add_model_performance(self, model_name, accuracy, precision, recall, f1_score):
        """
        Add model performance metrics.

        Args:
            model_name (str): Model name
            accuracy (float): Accuracy score
            precision (float): Precision score
            recall (float): Recall score
            f1_score (float): F1 score

        Returns:
            int: Performance record ID
        """
        try:
            self.cursor.execute("""
                INSERT INTO model_performance 
                (model_name, accuracy, precision, recall, f1_score)
                VALUES (?, ?, ?, ?, ?)
            """, (model_name, accuracy, precision, recall, f1_score))
            self.connection.commit()
            perf_id = self.cursor.lastrowid
            logger.info(f"Performance metrics added with ID: {perf_id}")
            return perf_id
        except sqlite3.Error as e:
            logger.error(f"Error adding performance metrics: {e}")
            return None

    def get_patient(self, patient_id):
        """
        Get patient information.

        Args:
            patient_id (int): Patient ID

        Returns:
            dict: Patient information
        """
        try:
            self.cursor.execute("""
                SELECT * FROM patients WHERE patient_id = ?
            """, (patient_id,))
            row = self.cursor.fetchone()
            if row:
                return {
                    'patient_id': row[0],
                    'name': row[1],
                    'age': row[2],
                    'gender': row[3],
                    'contact': row[4],
                    'created_at': row[5]
                }
            return None
        except sqlite3.Error as e:
            logger.error(f"Error retrieving patient: {e}")
            return None

    def get_patient_predictions(self, patient_id):
        """
        Get all predictions for a patient.

        Args:
            patient_id (int): Patient ID

        Returns:
            list: List of predictions
        """
        try:
            self.cursor.execute("""
                SELECT p.prediction_id, p.predicted_class, p.confidence, 
                       p.prediction_date, m.image_path
                FROM predictions p
                JOIN medical_images m ON p.image_id = m.image_id
                WHERE p.patient_id = ?
                ORDER BY p.prediction_date DESC
            """, (patient_id,))
            rows = self.cursor.fetchall()
            return [
                {
                    'prediction_id': row[0],
                    'predicted_class': row[1],
                    'confidence': row[2],
                    'prediction_date': row[3],
                    'image_path': row[4]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving patient predictions: {e}")
            return []

    def get_all_predictions(self):
        """
        Get all predictions from database.

        Returns:
            list: List of all predictions
        """
        try:
            self.cursor.execute("""
                SELECT prediction_id, patient_id, model_name, predicted_class, 
                       confidence, prediction_date
                FROM predictions
                ORDER BY prediction_date DESC
            """)
            rows = self.cursor.fetchall()
            return [
                {
                    'prediction_id': row[0],
                    'patient_id': row[1],
                    'model_name': row[2],
                    'predicted_class': row[3],
                    'confidence': row[4],
                    'prediction_date': row[5]
                }
                for row in rows
            ]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving predictions: {e}")
            return []

    def close(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
