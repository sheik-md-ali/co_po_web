import pandas as pd
import sys
sys.path.append('D:/project_clg/co_po_web/co_po_web')
from website.models import CoAttainment
from website import db

def read_excel_data(file_path):
    # Read the entire Excel file into a DataFrame
    df = pd.read_excel(file_path)
    
    # Find the row index where the column names start
    column_header_row = None
    for i, row in df.iterrows():
        if "SNO" in row.values and "REG NO" in row.values and "STUDENT NAME" in row.values:
            column_header_row = i
            break
    
    if column_header_row is None:
        raise ValueError("Column headers SNO, STUDENT NAME, and REG NO not found in the Excel file")
    
    # Set the correct row as header
    df.columns = df.iloc[column_header_row]
    df = df[column_header_row + 1:]
    
    # Drop any rows that are completely NaN
    df.dropna(how='all', inplace=True)
    
    # Ensure 'SNO' and 'REG NO' columns are of correct types
    df = df.astype({"SNO": int, "REG NO": int})
    
    # Identify question columns
    question_columns = [col for col in df.columns if col not in ['SNO', 'STUDENT NAME', 'REG NO']]
    
    # Convert question columns to float
    df[question_columns] = df[question_columns].astype(float)
    
    # Replace null values with 0
    df.fillna(0, inplace=True)
    
    return df.to_dict('records')


# Fetch CoAttainment record (example assuming there's a record with id=1)

loa_data = [{"max": "100", "min": "60", "level": "3"}, {"max": "59", "min": "50", "level": "2"}, {"max": "49", "min": "40", "level": "1"}, {"max": "39", "min": "0", "level": "0"}]


def calculate_level_of_attainment(percentage, loa_data):
    for level_info in loa_data:
        max_value = float(level_info['max'])
        min_value = float(level_info['min'])
        if min_value <= percentage <= max_value:
            return int(level_info['level'])
    return 0  # Default return value if no range matches



def create_mapping(mapping_dict, marks_data):
    individual_mapping = {}
    co_student_attainments = {}
    
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
            acquired_marks = student.get(question_key, 0)  # Use .get() to handle missing keys
            
            if co not in co_totals:
                co_totals[co] = {'acquired_marks': 0, 'total_weightage': 0}
            
            co_totals[co]['acquired_marks'] += acquired_marks
            co_totals[co]['total_weightage'] += max_marks
        
        # Calculate percentage and level of attainment for each CO
        for co, totals in co_totals.items():
            acquired_marks = totals['acquired_marks']
            total_weightage = totals['total_weightage']
            percentage = (acquired_marks / total_weightage) * 100 if total_weightage != 0 else 0
            level_of_attainment = calculate_level_of_attainment(percentage, loa_data)
             
            # Store individual CO attainment
            mapping_key = f'{reg_no}_{co}'
            individual_mapping[mapping_key] = {
                'acquired_marks': acquired_marks,
                'total_weightage': total_weightage,
                'percentage': percentage,
                'level_of_attainment': level_of_attainment
            }
            
            # Track the level of attainment for each student for each CO
            if co not in co_student_attainments:
                co_student_attainments[co] = []
            co_student_attainments[co].append(level_of_attainment)
    
    overall_mapping = {}
    # Calculate average level of attainment for each CO
    for co, attainments in co_student_attainments.items():
        average_level_of_attainment = sum(attainments) / len(attainments)
        
        overall_mapping[co] = {
            'average_level_of_attainment': average_level_of_attainment
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
    "Q9": {"co": "CO2", "maxMarks": "8"}, "Q10": {"co": "CO3", "maxMarks": "8"}
}

# Generate the mapping
individual_mapping, overall_mapping = create_mapping(mapping_dict, marks_data)

# Print individual and overall mappings
print("Individual CO Mappings:")
print(individual_mapping)
print("\nOverall CO Mappings:")
print(overall_mapping)
