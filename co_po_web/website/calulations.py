import pandas as pd

def read_excel_data(file_path):
    # Read the entire Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Find the row index where the column names start
    column_header_row = None
    for i, row in df.iterrows():
        if "SNO" in row.values and "REG NO" in row.values:
            column_header_row = i
            break
    
    if column_header_row is None:
        raise ValueError("Column headers SNO and REG NO not found in the Excel file")
    
    # Set the correct row as header
    df.columns = df.iloc[column_header_row]
    df = df[column_header_row + 1:]
    
    # Drop any rows that are completely NaN
    df.dropna(how='all', inplace=True)
    
    # Ensure 'SNO' and 'REG NO' columns are of correct types
    df = df.astype({"SNO": int, "REG NO": int})
    
    # Identify question columns
    question_columns = [col for col in df.columns if col not in ['SNO', 'REG NO']]
    
    # Convert question columns to float
    df[question_columns] = df[question_columns].astype(float)
    
    # Replace null values with 0
    df.fillna(0, inplace=True)
    
    return df.to_dict('records')


def calculate_level_of_attainment(percentage):
    if percentage >= 60:
        return 3 
    elif percentage >= 50:
        return 2
    elif percentage >=40:
        return 1
    else:
        return 0  


def create_mapping(mapping_dict, marks_data):
    individual_mapping = {}
    overall_totals = {}
    
    # Iterate through each student's marks
    for student in marks_data:
        reg_no = student['REG NO']
        
        # Dictionary to keep track of total marks and weightage for each CO
        co_totals = {}
        
        # Iterate through each question in the mapping dictionary
        for question, co_info in mapping_dict.items():
            question_key = question.upper()  # Ensure matching with the column headers in marks_data
            co = co_info['co']
            max_marks = float(co_info['maxMarks'])
            acquired_marks = student[question_key]
            
            if co not in co_totals:
                co_totals[co] = {'acquired_marks': 0, 'total_weightage': 0}
            
            co_totals[co]['acquired_marks'] += acquired_marks
            co_totals[co]['total_weightage'] += max_marks
        
        # Calculate percentage and level of attainment for each CO
        for co, totals in co_totals.items():
            acquired_marks = totals['acquired_marks']
            total_weightage = totals['total_weightage']
            percentage = (acquired_marks / total_weightage) * 100 if total_weightage != 0 else 0
            level_of_attainment = calculate_level_of_attainment(percentage)
            
            # Store individual CO attainment
            mapping_key = f'{reg_no}_{co}'
            individual_mapping[mapping_key] = {
                'acquired_marks': acquired_marks,
                'total_weightage': total_weightage,
                'percentage': percentage,
                'level_of_attainment': level_of_attainment
            }
            
            # Update overall CO totals
            if co not in overall_totals:
                overall_totals[co] = {'acquired_marks': 0, 'total_weightage': 0}
            overall_totals[co]['acquired_marks'] += acquired_marks
            overall_totals[co]['total_weightage'] += total_weightage
    
    overall_mapping = {}
    # Calculate overall CO attainment
    for co, totals in overall_totals.items():
        acquired_marks = totals['acquired_marks']
        total_weightage = totals['total_weightage']
        percentage = (acquired_marks / total_weightage) * 100 if total_weightage != 0 else 0
        level_of_attainment = calculate_level_of_attainment(percentage)
        
        overall_mapping[co] = {
            'acquired_marks': acquired_marks,
            'total_weightage': total_weightage,
            'percentage': percentage,
            'level_of_attainment': level_of_attainment
        }
    
    return individual_mapping, overall_mapping

# Example usage:
file_path = 'D:/project_clg/co_po_web/co_po_web/website/assessment_template (1).xlsx'
marks_data = read_excel_data(file_path)

mapping_dict = {
    "Q1": {"co": "CO1", "maxMarks": "2"}, "Q2": {"co": "CO1", "maxMarks": "2"},
    "Q3": {"co": "CO1", "maxMarks": "2"}, "Q4": {"co": "CO2", "maxMarks": "2"},
    "Q5": {"co": "CO2", "maxMarks": "2"}, "Q6": {"co": "CO1", "maxMarks": "8"},
    "Q7": {"co": "CO1", "maxMarks": "8"}, "Q8": {"co": "CO1", "maxMarks": "8"},
    "Q9": {"co": "CO2", "maxMarks": "8"}, "Q10": {"co": "CO2", "maxMarks": "8"}
}

# Generate the mapping
individual_mapping, overall_mapping = create_mapping(mapping_dict, marks_data)

# Print individual and overall mappings
print("Individual CO Mappings:")
print(individual_mapping)
print("\nOverall CO Mappings:")
print(overall_mapping)
