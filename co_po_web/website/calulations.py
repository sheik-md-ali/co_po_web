import pandas as pd
import sys
sys.path.append('D:/project_clg/co_po_web/co_po_web')
from website.models import AssessmentInstance, InternalAssessment, IAComponent, Assessment
from website import db
from io import BytesIO



def read_excel_data(file_data):
    df = pd.read_excel(file_data)
    column_header_row = None
    for i, row in df.iterrows():
        if "SNO" in row.values and "REG NO" in row.values:
            column_header_row = i
            break
    if column_header_row is None:
        raise ValueError("Column headers SNO, REG NO not found in the Excel file")
    df.columns = df.iloc[column_header_row]
    df = df[column_header_row + 1:]
    df.dropna(how='all', inplace=True)
    df = df.astype({"SNO": int, "REG NO": int})
    question_columns = [col for col in df.columns if col not in ['SNO', 'STUDENT NAME', 'REG NO']]
    for col in question_columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
        except Exception as e:
            print(f"Error processing column {col}: {e}")
            raise
    return df.to_dict('records')


def create_mapping(mapping_dict, marks_data, loa_data, target_percs):
    individual_mapping = {}
    co_student_attainments = {}
    co_target_met_count = {co: {'Y': 0, 'N': 0} for co in {co_info['co'] for co_info in mapping_dict.values()}}  # Initialize counts

    for student in marks_data:
        reg_no = student['REG NO']
        co_totals = {}

        for question, co_info in mapping_dict.items():
            question_key = question.upper()
            co = co_info['co']
            max_marks = float(co_info['maxMarks'])
            acquired_marks = student.get(question_key, 0)

            if co not in co_totals:
                co_totals[co] = {'acquired_marks': 0, 'total_weightage': 0}

            co_totals[co]['acquired_marks'] += acquired_marks
            co_totals[co]['total_weightage'] += max_marks

        for co, totals in co_totals.items():
            percentage = (totals['acquired_marks'] / totals['total_weightage']) * 100 if totals['total_weightage'] != 0 else 0
            level_of_attainment = calculate_level_of_attainment(percentage, loa_data[0])
            target_met = 'Y' if percentage >= target_percs else 'N'

            individual_mapping[f"{reg_no}_{co}"] = {
                'percentage': percentage,
                'level_of_attainment': level_of_attainment,
                'target_met': target_met
            }

            if co not in co_student_attainments:
                co_student_attainments[co] = []

            co_student_attainments[co].append(level_of_attainment)

            co_target_met_count[co][target_met] += 1

    overall_mapping = {
        co: {
            'average_level_of_attainment': round(sum(levels) / len(levels), 2) if levels else 0,
            'target_met_count': co_target_met_count[co],
            'total_students': len(marks_data)
        } for co, levels in co_student_attainments.items()
    }

    return individual_mapping, overall_mapping

def calculate_level_of_attainment(percentage, loa_data):
    for level_info in loa_data:
        max_value = float(level_info['max'])
        min_value = float(level_info['min'])
        if min_value <= percentage <= max_value:
            return int(level_info['level'])
    return 0

def calculate_co(internal_assessment_id):
    internal_assessment = InternalAssessment.query.get(internal_assessment_id)
    if not internal_assessment:
        return {}, {}, []

    assessment_instance_ids = internal_assessment.assessment_instance_ids

    co_data = {}
    target_count_data = {}
    all_cos = set()

    for instance_id in assessment_instance_ids:
        assessment_instance = AssessmentInstance.query.get(instance_id)
        if not assessment_instance or not assessment_instance.excel_file:
            continue

        excel_data = BytesIO(assessment_instance.excel_file)
        df = pd.read_excel(excel_data)

        header_row_index = df[df.iloc[:, 0] == 'COs'].index[0]
        co_table = df.iloc[header_row_index + 1:, :3]
        co_table.columns = ['COs', 'Values', 'Target_count']
        co_table = co_table.dropna(subset=['COs'])

        target_count_data[instance_id] = {}

        for _, row in co_table.iterrows():
            co = row['COs']
            value = row['Values']
            target_count = row['Target_count']

            if pd.isna(value):
                value = 0
            if pd.isna(target_count):
                target_count = 0

            all_cos.add(co)

            if co not in co_data:
                co_data[co] = []
            if co not in target_count_data[instance_id]:
                target_count_data[instance_id][co] = 0

            co_data[co].append(value)
            target_count_data[instance_id][co] += target_count

    # Calculate average CO values and round them to 2 decimal places
    co_data = {co: round(sum(values) / len(values), 2) for co, values in co_data.items()}

    # Sort COs dynamically based on all COs found
    predefined_order = sorted(all_cos)   
    sorted_co_data = {co: co_data[co] for co in predefined_order if co in co_data}
    sorted_target_count_data = {instance_id: {co: target_count_data[instance_id].get(co, 0) for co in predefined_order} for instance_id in target_count_data}

    return sorted_co_data, sorted_target_count_data, predefined_order

def calculate_co_weightage(internal_assessment_id):
    internal_assessment = InternalAssessment.query.get(internal_assessment_id)
    if not internal_assessment:
        return {}, {}, [], {}

    assessment_instance_ids = internal_assessment.assessment_instance_ids

    co_data = {}
    target_count_data = {}
    all_cos = set()
    cia_data = {}
    final_co_data = {}

    # Process each assessment instance
    for instance_id in assessment_instance_ids:
        assessment_instance = AssessmentInstance.query.get(instance_id)
        if not assessment_instance or not assessment_instance.excel_file:
            continue

        assessment = Assessment.query.filter_by(id=assessment_instance.assessment_id).first()
        ia_component = IAComponent.query.filter_by(id=assessment.ia_component_id).first()

        if not assessment or not ia_component:
            continue

        assessment_weightage = assessment.weightage
        cia_weightage = ia_component.weightage

        if ia_component.id not in cia_data:
            cia_data[ia_component.id] = {
                'weightage': cia_weightage,
                'total_weightage': 0,
                'co_data': {}
            }

        # Add assessment_weightage to the total_weightage
        cia_data[ia_component.id]['total_weightage'] += assessment_weightage

        excel_data = BytesIO(assessment_instance.excel_file)
        df = pd.read_excel(excel_data)

        header_row_index = df[df.iloc[:, 0] == 'COs'].index[0]
        co_table = df.iloc[header_row_index + 1:, :3]
        co_table.columns = ['COs', 'Values', 'Target_count']
        co_table = co_table.dropna(subset=['COs'])

        if instance_id not in target_count_data:
            target_count_data[instance_id] = {}

        for _, row in co_table.iterrows():
            co = row['COs']
            value = row['Values']
            target_count = row['Target_count']

            if pd.isna(value):
                value = 0
            if pd.isna(target_count):
                target_count = 0

            all_cos.add(co)

            if co not in cia_data[ia_component.id]['co_data']:
                cia_data[ia_component.id]['co_data'][co] = 0
            if co not in target_count_data[instance_id]:
                target_count_data[instance_id][co] = 0

            cia_data[ia_component.id]['co_data'][co] += value * (assessment_weightage / 100)
            target_count_data[instance_id][co] += target_count

    # Normalize the CO values for each CIA component
    for cia_id, cia_info in cia_data.items():
        for co, value in cia_info['co_data'].items():
            cia_info['co_data'][co] = (value / cia_info['total_weightage']) * 100

    # Calculate the final CO values
    for cia_id, cia_info in cia_data.items():
        for co, value in cia_info['co_data'].items():
            if co not in final_co_data:
                final_co_data[co] = 0
            final_co_data[co] += value * (cia_info['weightage'] / 100)

    # Sort COs dynamically based on all COs found
    predefined_order = sorted(all_cos)
    sorted_final_co_data = {co: round(final_co_data[co], 2) for co in predefined_order if co in final_co_data}
    sorted_target_count_data = {instance_id: {co: target_count_data[instance_id].get(co, 0) for co in predefined_order} for instance_id in target_count_data}

    return sorted_final_co_data, sorted_target_count_data, predefined_order
