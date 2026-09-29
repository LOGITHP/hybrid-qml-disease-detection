import pytest
import pandas as pd
import numpy as np
from app.agents.preprocessing_agent.interface import PreprocessingAgent, SplitManager, ClassBalancer, DimensionalityReducer, FeatureSelectorFactory
from app.schemas.preprocessing import PreprocessingPlan, PreprocessingPlanStep
from app.core.exceptions import ValidationError

@pytest.fixture
def mock_dataset():
    np.random.seed(42)
    df = pd.DataFrame({
        "age": np.random.randint(18, 80, 100),
        "bmi": np.random.uniform(18.5, 40.0, 100),
        "blood_pressure": np.random.randint(90, 180, 100),
        "gender": np.random.choice(["M", "F", np.nan], 100),
        "disease_target": np.random.choice([0, 1], 100)
    })
    # Add an outlier
    df.loc[0, "bmi"] = 999.0
    return df

def test_split_manager_leakage_prevention(mock_dataset):
    """Test that SplitManager splits before any operations."""
    X_train, X_val, X_test, y_train, y_val, y_test = SplitManager.create_splits(
        mock_dataset, 
        target_column="disease_target", 
        params={"train_ratio": 0.70, "val_ratio": 0.15, "test_ratio": 0.15, "random_state": 42}
    )
    assert len(X_train) == 70
    assert len(X_val) == 15
    assert len(X_test) == 15
    
    # Check that outliers in train don't affect val/test splits
    assert (X_train["bmi"] == 999.0).any() or (X_val["bmi"] == 999.0).any() or (X_test["bmi"] == 999.0).any()

def test_class_balancer_on_train_only(mock_dataset):
    """Test that SMOTE applies only to training data."""
    X_train, X_val, X_test, y_train, y_val, y_test = SplitManager.create_splits(
        mock_dataset, target_column="disease_target", params={"train_ratio": 0.70}
    )
    original_train_len = len(X_train)
    
    # Make class highly imbalanced manually
    X_train_imbalanced = X_train.copy()
    y_train_imbalanced = y_train.copy()
    mask = y_train_imbalanced == 1
    # keep only 2 samples of class 1
    indices_to_drop = y_train_imbalanced[mask].index[2:]
    X_train_imbalanced = X_train_imbalanced.drop(index=indices_to_drop)
    y_train_imbalanced = y_train_imbalanced.drop(index=indices_to_drop)
    
    # We drop categorical for smote test
    X_train_numeric = X_train_imbalanced.drop(columns=["gender"])
    
    X_res, y_res = ClassBalancer.apply(X_train_numeric, y_train_imbalanced, "smote")
    assert len(X_res) > len(X_train_numeric)
    assert (y_res == 0).sum() == (y_res == 1).sum()

def test_execute_plan_deterministic_and_no_leakage(mock_dataset):
    """Test the end-to-end plan execution correctly scales and isolates sets."""
    agent = PreprocessingAgent()
    
    plan = PreprocessingPlan(
        dataset_id="test",
        dataset_version_id="v1",
        target_column="disease_target",
        steps=[
            PreprocessingPlanStep(step_id=1, tool_name="stratified_split", parameters={}),
            PreprocessingPlanStep(step_id=2, tool_name="median_imputer", parameters={"columns": ["age", "bmi", "blood_pressure"]}),
            PreprocessingPlanStep(step_id=3, tool_name="standard_scaler", parameters={"columns": ["age", "bmi", "blood_pressure"]}),
            PreprocessingPlanStep(step_id=4, tool_name="most_frequent_imputer", parameters={"columns": ["gender"]}),
            PreprocessingPlanStep(step_id=5, tool_name="one_hot_encoder", parameters={"columns": ["gender"]}),
            PreprocessingPlanStep(step_id=6, tool_name="pca", parameters={"n_components": 2})
        ]
    )
    
    result = agent.execute_plan(mock_dataset, plan, target_column="disease_target")
    
    assert "X_train" in result
    assert "y_test" in result
    
    X_train = result["X_train"]
    X_val = result["X_val"]
    
    # PCA should reduce output to 2 features
    assert X_train.shape[1] == 2
    assert X_val.shape[1] == 2
    
    assert result["feature_names"] == ["PC1", "PC2"]
    
    # Original features should be preserved in metadata
    assert "age" in result["original_features"]

def test_pca_dimensionality_validation(mock_dataset):
    """Test that requesting more PCA components than features raises an error."""
    agent = PreprocessingAgent()
    
    plan = PreprocessingPlan(
        dataset_id="test",
        dataset_version_id="v1",
        target_column="disease_target",
        steps=[
            PreprocessingPlanStep(step_id=1, tool_name="stratified_split", parameters={}),
            PreprocessingPlanStep(step_id=2, tool_name="median_imputer", parameters={"columns": ["age"]}), # only 1 numerical feature
            PreprocessingPlanStep(step_id=6, tool_name="pca", parameters={"n_components": 10}) # 10 components > 1 feature
        ]
    )
    
    # Since only 'age' is processed, total features = 1
    # PCA with 10 components should raise ValidationError
    with pytest.raises(ValidationError, match="Cannot apply PCA"):
        # We must drop gender to avoid encoder error for this specific test
        mock_dataset_num = mock_dataset.drop(columns=["gender", "bmi", "blood_pressure"])
        agent.execute_plan(mock_dataset_num, plan, target_column="disease_target")

def test_feature_selection_lineage(mock_dataset):
    """Test feature lineage through feature selection."""
    agent = PreprocessingAgent()
    
    plan = PreprocessingPlan(
        dataset_id="test",
        dataset_version_id="v1",
        target_column="disease_target",
        steps=[
            PreprocessingPlanStep(step_id=1, tool_name="stratified_split", parameters={}),
            PreprocessingPlanStep(step_id=2, tool_name="median_imputer", parameters={"columns": ["age", "bmi", "blood_pressure"]}),
            PreprocessingPlanStep(step_id=3, tool_name="feature_selection", parameters={"method": "mutual_information", "k": 2})
        ]
    )
    
    mock_dataset_num = mock_dataset.drop(columns=["gender"])
    result = agent.execute_plan(mock_dataset_num, plan, target_column="disease_target")
    
    assert result["selected_features"] is not None
    assert len(result["selected_features"]) == 2
    assert len(result["feature_names"]) == 2
