import unittest
from src.data.loader import DataLoader
from src.data.preprocessor import DataPreprocessor

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DataLoader('path/to/dataset')
    
    def test_load_data(self):
        data = self.loader.load_data()
        self.assertIsNotNone(data)
        self.assertGreater(len(data), 0)

class TestDataPreprocessor(unittest.TestCase):
    def setUp(self):
        self.preprocessor = DataPreprocessor()
    
    def test_clean_data(self):
        raw_data = {'column1': [1, None, 3], 'column2': [4, 5, None]}
        cleaned_data = self.preprocessor.clean_data(raw_data)
        self.assertNotIn(None, cleaned_data['column1'])
        self.assertNotIn(None, cleaned_data['column2'])

    def test_feature_extraction(self):
        raw_data = {'column1': [1, 2, 3], 'column2': [4, 5, 6]}
        features = self.preprocessor.extract_features(raw_data)
        self.assertIn('feature1', features)
        self.assertEqual(features['feature1'], [5, 7, 9])  # Example feature extraction logic

if __name__ == '__main__':
    unittest.main()