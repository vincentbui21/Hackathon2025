import pandas as pd
import os
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.metrics import classification_report, roc_auc_score, mean_squared_error, r2_score
from xgboost import XGBClassifier
import seaborn as sns
import matplotlib.pyplot as plt

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Define file paths
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
CSV_FILES = {
    'purchases': 'valio_aimo_purchases_junction_2025.csv',
#    'replacement_orders': 'valio_aimo_replacement_orders_junction_2025.csv',
    'sales_deliveries': 'valio_aimo_sales_and_deliveries_junction_2025.csv'
}


def load_valio_data():
    """Load all Valio CSV files into DataFrames"""
    dataframes = {}
    
    for key, filename in CSV_FILES.items():
        file_path = os.path.join(BASE_PATH, filename)
        try:
            df = pd.read_csv(file_path)
            dataframes[key] = df
            print(f"✓ Loaded {key}: {df.shape[0]} rows, {df.shape[1]} columns")
        except FileNotFoundError:
            print(f"✗ Error: {filename} not found")
        except Exception as e:
            print(f"✗ Error loading {filename}: {e}")
    
    return dataframes

def explore_data(df, name="Dataset"):
    """Display basic info about DataFrame"""
    print(f"\n--- {name} ---")
    print(f"Shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}")
    print(f"Data types:\n{df.dtypes}")
    print(f"First rows:\n{df.head()}")

def add_not_delivered_qty(df,
                          order_col='order_qty',
                          delivered_col='delivered_qty',
                          new_col='not_delivered_qty',
                          flag_col='is_incomplete'):
    """
    Add a column with quantity not delivered (order_qty - delivered_qty)
    and a boolean flag for incomplete orders (positive not-delivered qty).
    Returns incomplete_count.
    """
    
    # treat missing values as 0 for the subtraction
    df[new_col] = df[order_col].fillna(0) - df[delivered_col].fillna(0)
    # mark incomplete where remaining qty is strictly positive (not zero, not negative)
    df[flag_col] = df[new_col] > 0
    incomplete_count = int(df[flag_col].sum())
    
    return incomplete_count

def top_products(df, product_col='product_code', top_n=40):
    """
    Count distinct products and display top N product codes only (no frequencies).
    """
    total_distinct = df[product_col].nunique()
    print(f"\nTotal distinct products: {total_distinct}")
    
    top_products_list = df[product_col].value_counts().head(top_n).index.tolist()
    print(f"\nTop {top_n} products (product codes only):")
    for code in top_products_list:
        print(code)
    
    return total_distinct, top_products_list

def add_delivered_status(df, new_col='under_delivered'):
    """
    Add a boolean column indicating if delivered_qty is less than order_qty.
    Converts values to integers: 1 if under-delivered, 0 if not.
    """
    df[new_col] = (df["delivered_qty"] < df["order_qty"]).astype(int)
    
def create_dates(df):
    """
    Convert date (DD-MM-YY) and time (HHMMSS as integer) columns to proper datetime.
    Handles cases where time might be missing or invalid.
    """
    df['order_created_date'] = pd.to_datetime(df['order_created_date'], errors='coerce')
    df['order_year'] = df['order_created_date'].dt.year
    df['order_month'] = df['order_created_date'].dt.month
    df['order_day'] = df['order_created_date'].dt.day
    df['order_day_of_week'] = df['order_created_date'].dt.dayofweek  # Monday=0, Sunday=6
    df['order_day_of_year'] = df['order_created_date'].dt.dayofyear
    df['order_week_of_year'] = df['order_created_date'].dt.isocalendar().week
    df['is_holiday_season'] = df['order_month'].isin([11, 12]).astype(int)  # Nov-Dec
    df['is_summer'] = df['order_month'].isin([6, 7, 8]).astype(int)

def add_vendor_to_sales_safe(sales_deliveries, purchases, product_col='product_code', 
                            vendor_source_col='customer_number', vendor_target_col='supplier_name'):
    """
    Add vendor information without overwriting existing customer_number column
    Uses a different column name like 'supplier_name'
    """
    
    print("Before adding vendor info:")
    print(f"Sales deliveries columns: {sales_deliveries.columns.tolist()}")
    print(f"Sales deliveries shape: {sales_deliveries.shape}")
    
    # Check for duplicate products with different suppliers in purchases
    product_supplier_counts = purchases.groupby(product_col)[vendor_source_col].nunique()
    multi_supplier_products = product_supplier_counts[product_supplier_counts > 1]
    
    if len(multi_supplier_products) > 0:
        print(f"\n⚠️ Warning: {len(multi_supplier_products)} products have multiple suppliers:")
        print(multi_supplier_products.head())
    
    # Get unique product-supplier mapping
    product_supplier_map = purchases.groupby(product_col)[vendor_source_col].agg(
        lambda x: x.mode().iloc[0] if len(x.mode()) > 0 else x.iloc[0]
    ).reset_index()
    
    # Rename the column to avoid conflict
    product_supplier_map = product_supplier_map.rename(columns={vendor_source_col: vendor_target_col})
    
    # Merge with sales_deliveries
    sales_with_supplier = sales_deliveries.merge(
        product_supplier_map,
        on=product_col,
        how='left'
    )
    
    # Check results
    missing_supplier_count = sales_with_supplier[vendor_target_col].isna().sum()
    print(f"\nAfter adding supplier info:")
    print(f"Sales deliveries shape: {sales_with_supplier.shape}")
    print(f"Records with supplier: {len(sales_with_supplier) - missing_supplier_count}")
    print(f"Records missing supplier: {missing_supplier_count} ({missing_supplier_count/len(sales_with_supplier):.1%})")
    
    # Show sample data with both customer and supplier info
    print(f"\nSample records showing both customer and supplier:")
    sample_data = sales_with_supplier[['product_code', 'customer_number', vendor_target_col]].dropna().head(10)
    for idx, row in sample_data.iterrows():
        print(f"  Product: {row['product_code']} → Customer: {row['customer_number']} → Supplier: {row[vendor_target_col]}")
    
    return sales_with_supplier

def calculate_product_delivery_rates(df, product_col='product_code', 
                                   order_col='order_qty', 
                                   delivered_col='delivered_qty'):
    """
    Calculate delivery success rates for each product
    """
    
    # Create delivery success flag (100% delivered = successful)
    df['delivery_success'] = (df[delivered_col] >= df[order_col]).astype(int)
    
    # Calculate delivery ratio (0-1 scale)
    df['delivery_ratio'] = df[delivered_col] / df[order_col].replace(0, 1)
    df['delivery_ratio'] = df['delivery_ratio'].clip(upper=1.0)  # Cap at 100%
    
    # Calculate product-level statistics
    product_stats = df.groupby([product_col, 'supplier_name']).agg({
        'delivery_success': ['count', 'mean', 'sum'],
        'delivery_ratio': ['mean', 'std', 'min', 'max'],
        order_col: 'sum',
        delivered_col: 'sum'
    }).round(4)
    
    # Flatten column names
    product_stats.columns = [
        'total_orders', 
        'success_rate', 
        'successful_orders',
        'avg_delivery_ratio', 
        'delivery_std', 
        'min_delivery_ratio',
        'max_delivery_ratio',
        'total_ordered_qty', 
        'total_delivered_qty'
    ]
    
    product_stats = product_stats.reset_index()
    
    # Calculate additional metrics
    product_stats['delivery_efficiency'] = (
        product_stats['total_delivered_qty'] / product_stats['total_ordered_qty']
    ).round(4)
    
    # Sort by success rate (descending)
    product_stats = product_stats.sort_values('success_rate', ascending=False)
    
    return product_stats

def get_success_categories_with_details(product_stats):
    """
    Returns product_code, supplier_name, and success_rate for all three success categories
    """
    success_95_98 = product_stats[
        (product_stats['success_rate'] > 0.97) &
        (product_stats['success_rate'] < 0.98)
    ][['product_code', 'supplier_name', 'success_rate']].head(20)
    
    success_94_92 = product_stats[
        (product_stats['success_rate'] > 0.95) &
        (product_stats['success_rate'] < 0.96)
    ][['product_code', 'supplier_name', 'success_rate']].head(10)
    
    success_90 = product_stats[
        (product_stats['success_rate'] > 0.93) &
        (product_stats['success_rate'] < 0.94)][['product_code', 'supplier_name', 'success_rate']].head(10)
    
    # Combine all into one list of dictionaries with proper type conversion
    all_products_list = []
    
    # Add products from each category with type conversion
    for idx, row in success_95_98.iterrows():
        all_products_list.append({
            'ProductID': int(row['product_code']),
            'ProducerID': int(row['supplier_name']),
            'Prediction_score': float(100*row['success_rate']),
        })
    
    for idx, row in success_94_92.iterrows():
        all_products_list.append({
            'ProductID': int(row['product_code']),
            'ProducerID': int(row['supplier_name']),
            'Prediction_score': float(100*row['success_rate']),
        })
    
    for idx, row in success_90.iterrows():
        all_products_list.append({
            'ProductID': int(row['product_code']),
            'ProducerID': int(row['supplier_name']),
            'Prediction_score': float(100*row['success_rate']),
        })
    
    return all_products_list
    
def get_connection():
            try:
                connection = mysql.connector.connect(
                    host=os.getenv("DB_HOST"),
                    user=os.getenv("DB_USER"),
                    password=os.getenv("DB_PASSWORD"),
                    database=os.getenv("DB_NAME"),
                )

                if connection.is_connected():
                    return connection

            except Error as e:
                print("❌ Database connection failed:", e)
                return None
            
# Main execution
if __name__ == "__main__":
    # Load all data
    data = load_valio_data()
    
    if 'sales_deliveries' in data:
        # incomplete_count = add_not_delivered_qty(data['sales_deliveries'])
        # print(f"\nNot-delivered column added. Incomplete orders count: {incomplete_count}")
        
        # # Show top 40 product codes (no frequencies)
        # total_distinct, top_40 = top_products(data['sales_deliveries'], top_n=40)
        sales_deliveries = data["sales_deliveries"]
        purchases = data["purchases"]
        
        add_delivered_status(sales_deliveries)
        
        sales_deliveries = add_vendor_to_sales_safe(sales_deliveries, purchases) 
        
        create_dates(sales_deliveries)  
        product_stats = calculate_product_delivery_rates(sales_deliveries)
        
        success_categories = get_success_categories_with_details(product_stats)
    
        df = pd.DataFrame(success_categories)
        print(df)

        # #create_datetime_column(sales_deliveries)
        # features = [
        #     "product_code",
        #     "order_qty",
        #     "order_year",
        #     "order_month",
        #     "order_day",
        #     "order_day_of_week",
        #     "order_day_of_year",        
        #     "order_week_of_year",
        #     "order_created_time",
        #     "is_holiday_season",
        #     "is_summer"
        # ]
        # X = sales_deliveries[features]
        # y = sales_deliveries["under_delivered"]
        
        # X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, shuffle=True)
        
        # model = XGBClassifier(
        #     n_estimators=300,
        #     learning_rate=0.05,
        #     max_depth=6,
        #     subsample=0.8,
        #     colsample_bytree=0.8,
        #     eval_metric="logloss",
        # )

        # model.fit(X_train, y_train)
        
        # #plt.figure(figsize=(12, 8))
        # #sns.heatmap(data=sales_deliveries[features].corr(), annot=True, fmt=".2f", cmap="coolwarm")
        # #plt.show()
        
        # y_pred = model.predict(X_test)
        # y_prob = model.predict_proba(X_test)[:, 1]  # Probability of shortage

        # print(classification_report(y_test, y_pred))
        # print("ROC AUC:", roc_auc_score(y_test, y_prob))
        
        # dt_model = DecisionTreeClassifier(
        #     random_state=42,
        #     max_depth=5,  # Prevent overfitting
        #     min_samples_split=10,
        #     min_samples_leaf=5
        # )
        
        # dt_model.fit(X_train, y_train)
        # y_pred_treeclass = dt_model.predict(X_test)
        
        # # Evaluate the model
        # accuracy = accuracy_score(y_test, y_pred_treeclass)
        # print(f"Accuracy of decision tree: {accuracy:.4f}")
        # print("\nClassification Report:")
        # print(classification_report(y_test, y_pred_treeclass,zero_division=0))
        
        # # Initialize and train regression tree
        # dt_regressor = DecisionTreeRegressor(
        #     random_state=42,
        #     max_depth=5,
        #     min_samples_split=10,
        #     min_samples_leaf=5
        # )

        # dt_regressor.fit(X_train, y_train)
        # y_pred_treereg = dt_regressor.predict(X_test)

        # # Evaluate regression model
        # mse = mean_squared_error(y_test, y_pred_treereg)
        # r2 = r2_score(y_test, y_pred_treereg)
        # print(f"Mean Squared Error: {mse:.4f}")
        # print(f"R² Score: {r2:.4f}")
        
        # rf_model = RandomForestClassifier(
        #     n_estimators=200,
        #     max_depth=10,
        #     min_samples_split=5,
        #     min_samples_leaf=3,
        #     class_weight='balanced',  # Handles imbalance
        #     random_state=42,
        #     n_jobs=-1
        # )

        # rf_model.fit(X_train, y_train)
        # y_pred_rf = rf_model.predict(X_test)
        # print("Random Forest Report:")
        # print(classification_report(y_test, y_pred_rf, zero_division=0))