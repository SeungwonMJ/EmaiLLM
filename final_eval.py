def evaluate_email_classification(all_qtm_emails, output):
    """
    Evaluate email classification performance with comprehensive metrics
    for multi-label (first half) and single-label (second half) data.
    
    Parameters:
    - all_qtm_emails: List of email data with ground truth labels in 'category' field
    - output: List of model prediction data with 'predicted_classification' field
    
    Returns:
    - Dictionary containing all metrics for different segments of the dataset
    """
    # Get total length of dataset
    length = len(all_qtm_emails)
    first_half_end = 65  # Index where first half ends
    
    # Define metrics calculation functions
    def calculate_jaccard(predicted_keywords, true_keywords):
        pred_set = set(predicted_keywords)
        true_set = set(true_keywords)
        
        intersection = len(pred_set & true_set)
        union = len(pred_set | true_set)
        
        return intersection / union if union > 0 else 1.0  # If both sets empty, similarity is 1
    
    def calculate_precision(predicted_keywords, true_keywords):
        pred_set = set(predicted_keywords)
        true_set = set(true_keywords)
        
        intersection = len(pred_set & true_set)
        
        return intersection / len(pred_set) if len(pred_set) > 0 else 1.0  # If no predictions, precision is 1
    
    def calculate_recall(predicted_keywords, true_keywords):
        pred_set = set(predicted_keywords)
        true_set = set(true_keywords)
        
        intersection = len(pred_set & true_set)
        
        return intersection / len(true_set) if len(true_set) > 0 else 1.0  # If no true labels, recall is 1
    
    def calculate_f1(predicted_keywords, true_keywords):
        precision = calculate_precision(predicted_keywords, true_keywords)
        recall = calculate_recall(predicted_keywords, true_keywords)
        
        return 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    def calculate_accuracy(predicted_keywords, true_keywords):
        """For single-label classification, checks if the prediction contains the true label"""
        return 1.0 if set(true_keywords) & set(predicted_keywords) else 0.0
    
    # Calculate per-example metrics for different segments
    def calculate_segment_metrics(start_idx, end_idx):
        total_precision = 0
        total_recall = 0
        total_f1 = 0
        total_jaccard = 0
        total_accuracy = 0  # Only meaningful for single-label
        
        for i in range(start_idx, end_idx):
            predicted = output[i]["predicted_classification"]["relevant_keywords"]
            true = all_qtm_emails[i]["category"]
            
            total_precision += calculate_precision(predicted, true)
            total_recall += calculate_recall(predicted, true)
            total_f1 += calculate_f1(predicted, true)
            total_jaccard += calculate_jaccard(predicted, true)
            total_accuracy += calculate_accuracy(predicted, true)
        
        num_examples = end_idx - start_idx
        return {
            "precision": total_precision / num_examples if num_examples > 0 else 0,
            "recall": total_recall / num_examples if num_examples > 0 else 0,
            "f1": total_f1 / num_examples if num_examples > 0 else 0,
            "jaccard": total_jaccard / num_examples if num_examples > 0 else 0,
            "accuracy": total_accuracy / num_examples if num_examples > 0 else 0
        }
    
    # Calculate global metrics for second half (single-label)
    def calculate_global_metrics_second_half():
        total_tp, total_fp, total_fn = 0, 0, 0
        total_correct = 0
        
        for i in range(first_half_end, length):
            predicted = set(output[i]["predicted_classification"]["relevant_keywords"])
            true = set(all_qtm_emails[i]["category"])
            
            # Calculate TP, FP, FN for global metrics
            tp = len(predicted & true)
            fp = len(predicted - true)
            fn = len(true - predicted)
            
            total_tp += tp
            total_fp += fp
            total_fn += fn
            
            # For accuracy
            if tp > 0:
                total_correct += 1
        
        # Calculate global metrics
        precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
        recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = total_correct / (length - first_half_end) if (length - first_half_end) > 0 else 0
        
        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "accuracy": accuracy
        }
    
    # Calculate confusion matrix for second half (single-label)
    def calculate_confusion_matrix():
        # Get all unique categories
        all_categories = set()
        for email in all_qtm_emails:
            all_categories.update(email["category"])
        all_categories = sorted(list(all_categories))
        
        # Initialize confusion matrix
        confusion_matrix = {category: {pred: 0 for pred in all_categories} for category in all_categories}
        
        # Fill confusion matrix
        for i in range(first_half_end, length):
            true_category = all_qtm_emails[i]["category"][0]  # Assuming single label
            
            # Find predicted category
            predicted = output[i]["predicted_classification"]["relevant_keywords"]
            predicted_category = predicted[0] if predicted else None  # Take first prediction
            
            # Update confusion matrix
            if predicted_category in all_categories:
                confusion_matrix[true_category][predicted_category] += 1
        
        return confusion_matrix
    
    # Calculate all metrics
    first_half_metrics = calculate_segment_metrics(0, first_half_end)
    second_half_metrics = calculate_segment_metrics(first_half_end, length)
    whole_dataset_metrics = calculate_segment_metrics(0, length)
    second_half_global_metrics = calculate_global_metrics_second_half()
    confusion_matrix = calculate_confusion_matrix()
    
    # Compile results
    results = {
        "first_half": first_half_metrics,
        "second_half": {
            "per_example": second_half_metrics,
            "global": second_half_global_metrics
        },
        "whole_dataset": whole_dataset_metrics,
        "confusion_matrix": confusion_matrix
    }
    
    return results

# Example usage
def print_evaluation_report(all_qtm_emails, output):
    """
    Generate and print a comprehensive evaluation report
    """
    results = evaluate_email_classification(all_qtm_emails, output)
    
    print("=" * 80)
    print("EMAIL CLASSIFICATION EVALUATION REPORT")
    print("=" * 80)
    
    print("\nPER-EXAMPLE METRICS:")
    print("-" * 80)
    print(f"{'Metric':<15} {'First Half':<15} {'Second Half':<15} {'Whole Dataset':<15}")
    print("-" * 80)
    metrics = ["precision", "recall", "f1", "jaccard", "accuracy"]
    for metric in metrics:
        first_half_val = results["first_half"].get(metric, "N/A")
        second_half_val = results["second_half"]["per_example"].get(metric, "N/A")
        whole_val = results["whole_dataset"].get(metric, "N/A")
        
        if first_half_val != "N/A":
            first_half_val = f"{first_half_val:.2f}"
        if second_half_val != "N/A":
            second_half_val = f"{second_half_val:.2f}"
        if whole_val != "N/A":
            whole_val = f"{whole_val:.2f}"
        
        print(f"{metric.capitalize():<15} {first_half_val:<15} {second_half_val:<15} {whole_val:<15}")
    
    print("\nGLOBAL METRICS FOR SECOND HALF:")
    print("-" * 80)
    for metric, value in results["second_half"]["global"].items():
        print(f"{metric.capitalize():<15} {value:.2f}")
    
    print("\nCONFUSION MATRIX SUMMARY (TOP MISCLASSIFICATIONS):")
    print("-" * 80)
    # Find top confused category pairs
    top_confusions = []
    for true_cat, predictions in results["confusion_matrix"].items():
        for pred_cat, count in predictions.items():
            if true_cat != pred_cat and count > 0:
                top_confusions.append((true_cat, pred_cat, count))
    
    # Sort by count descending and print top 5
    top_confusions.sort(key=lambda x: x[2], reverse=True)
    for true_cat, pred_cat, count in top_confusions[:5]:
        print(f"True: {true_cat}, Predicted: {pred_cat}, Count: {count}")
    
    print("=" * 80)

def evaluate_experiment_results():
    """
    Evaluate all experiment results and present them in a comprehensive table format.
    
    Table structure:
    - Two main columns: Without Keyword Count Control, With Keyword Count Control
    - Three sub-columns for each condition: Zero-shot, Five-shot, Eight-shot
    - Three sub-sub-columns for each shot type: First Half, Second Half, Whole Dataset
    - Five metrics for each segment: Precision, Recall, F1, Jaccard, Accuracy
    """
    import os
    import json
    from tabulate import tabulate
    
    # Define experiment paths
    base_path = '/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/final_experiments'
    conditions = ["without_keyword_count_control", "with_keyword_count_control"]
    shots = ["0shot", "5shot", "8shot"]
    
    # Load all QTM emails for reference
    with open('/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/data/qtm_emails_final_version.json', 'r') as f:
        all_qtm_emails = json.load(f)
    
    # Organize data for table
    results = {}
    for condition in conditions:
        results[condition] = {}
        for shot in shots:
            file_path = os.path.join(base_path, f"{condition}_{shot}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    output = json.load(f)
                    # Evaluate results
                    eval_results = evaluate_email_classification(all_qtm_emails, output)
                    results[condition][shot] = eval_results
            else:
                print(f"Warning: File not found: {file_path}")
    
    # Extract metrics for each segment and format table
    metrics = ["precision", "recall", "f1", "jaccard", "accuracy"]
    segments = ["first_half", "second_half", "whole_dataset"]
    segment_labels = ["First Half", "Second Half", "Whole Dataset"]
    
    # Prepare header row
    headers = ["Metric"]
    for cond in conditions:
        cond_name = "Without Count Control" if "without" in cond else "With Count Control"
        for shot in shots:
            shot_name = shot.replace("shot", "-Shot")
            for seg in segment_labels:
                headers.append(f"{cond_name}\n{shot_name}\n{seg}")
    
    # Prepare table rows
    table_data = []
    for metric in metrics:
        row = [metric.capitalize()]
        for cond in conditions:
            for shot in shots:
                if cond in results and shot in results[cond]:
                    # First half
                    val = results[cond][shot]["first_half"].get(metric, "N/A")
                    row.append(f"{val:.2f}" if isinstance(val, float) else val)
                    
                    # Second half (use per_example metrics)
                    val = results[cond][shot]["second_half"]["per_example"].get(metric, "N/A")
                    row.append(f"{val:.2f}" if isinstance(val, float) else val)
                    
                    # Whole dataset
                    val = results[cond][shot]["whole_dataset"].get(metric, "N/A")
                    row.append(f"{val:.2f}" if isinstance(val, float) else val)
                else:
                    # If data missing, add placeholders
                    row.extend(["N/A", "N/A", "N/A"])
        table_data.append(row)
    
    # Generate table
    table = tabulate(table_data, headers=headers, tablefmt="grid")
    print("\nCOMPREHENSIVE EVALUATION RESULTS:\n")
    print(table)
    
    # Save table to file
    with open(os.path.join(base_path, 'evaluation_results_table.txt'), 'w') as f:
        f.write("COMPREHENSIVE EVALUATION RESULTS:\n\n")
        f.write(table)
    
    print(f"\nTable saved to {os.path.join(base_path, 'evaluation_results_table.txt')}")
    
    return results

# Add a main block to run the evaluation when script is executed directly
if __name__ == "__main__":
    import json
    
    # Check if we're evaluating a specific experiment or all experiments
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--all":
        # Evaluate all experiments
        evaluate_experiment_results()
    else:
        # Default behavior: evaluate the most recent experiment
        with open('/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/data/qtm_emails_final_version.json', 'r') as f:
            all_qtm_emails = json.load(f)
            
        with open('/Users/natehu/Desktop/QTM 329 Comp Ling/EmaiLLM/qtm_output_threeshot.json', 'r') as f:
            output = json.load(f)
            
        print_evaluation_report(all_qtm_emails, output)