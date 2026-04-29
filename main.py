import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import optuna
from catboost import CatBoostClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.metrics import f1_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.preprocessing import MinMaxScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# Thêm chữ r ở đây để tránh lỗi đường dẫn
DATA_PATH = r'D:\Slide 28 tech\Kì 2 năm 4\WA_Fn-UseC_-Telco-Customer-Churn.csv'

df = pd.read_csv(DATA_PATH)
pd.set_option('display.max_columns', None)

print(df.head(10))

df['SeniorCitizen'] = df['SeniorCitizen'].map({0: 'No', 1: 'Yes'})

df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
print(f'TotalCharges Colomn Type : {df['TotalCharges'].dtype}')
print(f'TotalCharges Missing Values : {df['TotalCharges'].isnull().sum()}')

df['TotalCharges'] = df['TotalCharges'].fillna(df['TotalCharges'].mean())
print(f'Shape : {df.shape}')
print(f'Missing values: {df.isnull().sum().sum()}')
print(f'Duplicated: {df.duplicated().sum()}')


print(df.describe(include='all'))

df.hist(figsize=(12,10))
plt.show()

num_cols = df.select_dtypes(include=['number']).columns

for col in num_cols:
    plt.figure(figsize=(6,4))
    sns.boxplot(x=df[col])
    plt.title(f'Boxplot of {col}')
    plt.xlabel(col)
    plt.grid(axis='x', linestyle='--', alpha=0.5)
    plt.show()


cat_cols = df.select_dtypes(include=['object']).columns.drop('customerID')
for col in cat_cols:
    plt.figure(figsize=(6,4))
    sns.countplot(x=col, data=df)
    plt.title(col)
    plt.xticks(rotation=45)
    plt.show()


for col in cat_cols:
    plt.figure(figsize=(6,4))
    sns.countplot(x=col, hue='Churn', data=df)
    plt.title(f'{col} vs Churn')
    plt.xticks(rotation=45)
    plt.show()

for col in num_cols:
    plt.figure()
    sns.boxplot(x='Churn', y=col, data=df)
    plt.title(f'{col} vs Churn')
    plt.show()


df['Churn'].value_counts(normalize=True) * 100

df['AvgCharges'] = df['TotalCharges'] / df['tenure']
df['AvgCharges'] = df['AvgCharges'].replace([np.inf, -np.inf], 0)
df['AvgCharges'] = df['AvgCharges'].fillna(0)


services = [
    'PhoneService', 'MultipleLines', 'InternetService',
    'OnlineSecurity', 'OnlineBackup', 'DeviceProtection',
    'TechSupport', 'StreamingTV', 'StreamingMovies'
]

df['TotalServices'] = (df[services] == 'Yes').sum(axis=1)


df['IsLongTerm'] = df['Contract'].apply(
    lambda x: 'Yes' if x != 'Month-to-month' else 'No'
)


df['ChargePerService'] = df['MonthlyCharges'] / (df['TotalServices'] + 1)

# Min-Max Scaling
scaler = MinMaxScaler()
num_cols_to_scale = ['tenure', 'MonthlyCharges', 'TotalCharges']
df[num_cols_to_scale] = scaler.fit_transform(df[num_cols_to_scale])

X = df.drop(columns=['customerID', 'Churn'])

y = df['Churn'].map({'No': 0, 'Yes': 1})

cat_cols = X.select_dtypes(exclude=['int64', 'float64']).columns.tolist()
cat_features = [X.columns.get_loc(col) for col in cat_cols]

# Encoding for Sklearn Models
X_encoded = pd.get_dummies(X, columns=cat_cols, drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, stratify=y, random_state=42
)

X_train_enc, X_test_enc, _, _ = train_test_split(
    X_encoded, y, test_size=0.3, stratify=y, random_state=42
)



def objective(trial):
    params = {
        'iterations': trial.suggest_int('iterations', 300, 800),
        'depth': trial.suggest_int('depth', 4, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1, 10),
        'loss_function': 'Logloss',
        'eval_metric': 'F1',
        'class_weights': [1, 73/27],
        'task_type': 'GPU',   
        'devices': '0',       
        'verbose': 0,
        'random_state': 42
    }

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    f1_scores = []

    for train_idx, val_idx in cv.split(X_train, y_train):

        model = CatBoostClassifier(**params) 
        
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model.fit(
            X_tr, y_tr,
            cat_features=cat_features,
            eval_set=(X_val, y_val),
            early_stopping_rounds=50,
            verbose=0,
            use_best_model=False
        )

        y_pred = model.predict(X_val)
        f1 = f1_score(y_val, y_pred)
        f1_scores.append(f1)

    return np.mean(f1_scores)


study = optuna.create_study(direction='maximize')

study.optimize(objective, n_trials=5)

best_params = study.best_params

print("Best Params:", best_params)
print("Best CV F1:", study.best_value)

# Final CatBoost Model training with best parameters
best_cat = CatBoostClassifier(**best_params, verbose=0)
best_cat.fit(X_train, y_train, cat_features=cat_features)
y_pred_cat = best_cat.predict(X_test)
f1_cat = f1_score(y_test, y_pred_cat)

# Confusion Matrix: CatBoost
cm_cat = confusion_matrix(y_test, y_pred_cat)
disp_cat = ConfusionMatrixDisplay(confusion_matrix=cm_cat, display_labels=['No', 'Yes'])
disp_cat.plot(cmap='Blues')
plt.title("Confusion Matrix: CatBoost")
plt.show()

# Feature Importance: CatBoost
plt.figure(figsize=(10, 8))
cat_importance = pd.Series(best_cat.get_feature_importance(), index=X.columns).sort_values(ascending=True)
cat_importance.plot(kind='barh', color='skyblue')
plt.title("Feature Importance: CatBoost")
plt.xlabel("Importance")
plt.show()


# Sklearn Models comparison
models = {
    'Logistic Regression': LogisticRegression(max_iter=1000),
    'Decision Tree': DecisionTreeClassifier(random_state=42),
    'Random Forest': RandomForestClassifier(random_state=42)
}

results = {'CatBoost': f1_cat}

print("\nModel Comparison and Evaluation:")
for name, model in models.items():
    model.fit(X_train_enc, y_train)
    y_pred = model.predict(X_test_enc)
    results[name] = f1_score(y_test, y_pred)
    print(f"\n{name} Results:")
    print(classification_report(y_test, y_pred))
    
    # Confusion Matrix
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['No', 'Yes'])
    disp.plot(cmap='Blues')
    plt.title(f"Confusion Matrix: {name}")
    plt.show()

    # Feature Importance for Random Forest
    if name == 'Random Forest':
        plt.figure(figsize=(10, 8))
        rf_importance = pd.Series(model.feature_importances_, index=X_encoded.columns).sort_values(ascending=True)
        rf_importance.tail(20).plot(kind='barh', color='salmon') # Show top 20
        plt.title(f"Feature Importance: {name} (Top 20)")
        plt.xlabel("Importance")
        plt.show()


print("\nSummary Comparison (F1-Score):")
for name, score in results.items():
    print(f"{name}: {score:.4f}")
