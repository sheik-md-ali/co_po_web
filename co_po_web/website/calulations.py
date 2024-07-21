import pandas as pd
import sys
sys.path.append('D:/project_clg/co_po_web/co_po_web')
from website.models import CoAttainment, AssessmentInstance, InternalAssessment
from website import db
from io import BytesIO

def calculate_co(internal_assessment_id):
    internal_assessment = InternalAssessment.query.get(internal_assessment_id)
    if not internal_assessment:
        return {}

    # Step 1: Retrieve the list of assessment instance IDs
    assessment_instance_ids = internal_assessment.assessment_instance_ids

    co_data = {}

    for instance_id in assessment_instance_ids:
        # Step 2: Fetch the corresponding records from the AssessmentInstance model
        assessment_instance = AssessmentInstance.query.get(instance_id)
        if not assessment_instance or not assessment_instance.excel_file:
            continue

        # Step 3: Retrieve the associated Excel file
        excel_data = BytesIO(assessment_instance.excel_file)
        df = pd.read_excel(excel_data)

        # Step 4: Extract the CO values and target counts from the last table
        co_table = df.iloc[-3:, -3:]
        co_table.columns = ['COs', 'Values', 'Target_count']

        # Step 5: Aggregate the CO values and target counts
        for _, row in co_table.iterrows():
            co = row['COs']
            value = row['Values']
            target_count = row['Target_count']

            if co not in co_data:
                co_data[co] = {'total_value': 0, 'total_target_count': 0}

            co_data[co]['total_value'] += value
            co_data[co]['total_target_count'] += target_count

    # Step 6: Return the aggregated data
    return co_data

# Example usage
internal_assessment_id = 1  # Replace with the actual internal assessment ID
result = calculate_co(internal_assessment_id)
print(result)