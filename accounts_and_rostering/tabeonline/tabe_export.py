__author__ = 'mattpauls'

import sys
import os
import csv
import re
from pathlib import Path
import time
# from fabric import Connection
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
import mysql.connector
from mysql.connector import Error

# Add FileMaker module to path. This probably isn't the best way to do it, but I spent way too much time trying to figure it out.
FM_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "filemaker_api")
sys.path.append(os.path.dirname(FM_DIR))

from filemaker_api.filemaker_api import filemaker_get_records  # noqa

c = Console()

load_dotenv()

# Set variables
classNo = str(os.getenv("CLASS_NUMBER"))
outputfolder = os.getenv("OUTPUT_FOLDER")
district_code = os.getenv("DISTRICT_CODE")
school_code = os.getenv("SCHOOL_CODE")
print("Output folder is:", outputfolder)

# MySQL configuration (used by export_post_tabe_14)
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")
MYSQL_USERNAME = os.getenv("MYSQL_USERNAME")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")

# NTA score ranges per subject and pre-test level.
# Source: TABE Next Test Assignment Post-Testing Chart (Forms 13/14).
# Each entry: (min_score, max_score, suggested_nta_level)
_NTA_RANGES = {
    'READ': {
        'E': [(300, 441, 'E'), (442, 500, 'E'), (501, 535, 'M')],
        'M': [(442, 500, 'M'), (501, 535, 'M'), (536, 575, 'D')],
        'D': [(501, 535, 'D'), (536, 575, 'D'), (576, 616, 'A')],
        'A': [(536, 575, 'A'), (576, 616, 'A'), (617, 800, 'A')],
    },
    'MATH': {
        'E': [(300, 448, 'E'), (449, 495, 'E'), (496, 536, 'M')],
        'M': [(449, 495, 'M'), (496, 536, 'M'), (537, 595, 'D')],
        'D': [(496, 536, 'D'), (537, 595, 'D'), (596, 656, 'A')],
        'A': [(537, 595, 'A'), (596, 656, 'A'), (657, 800, 'A')],
    },
    'LANG': {
        'E': [(300, 457, 'E'), (458, 510, 'E'), (511, 546, 'M')],
        'M': [(458, 510, 'M'), (511, 546, 'M'), (547, 583, 'D')],
        'D': [(511, 546, 'D'), (547, 583, 'D'), (584, 630, 'A')],
        'A': [(547, 583, 'A'), (584, 630, 'A'), (631, 800, 'A')],
    },
}


def _calculate_post_tabe_level(pre_level: str, score, subject: str) -> str | None:
    if not pre_level or score is None:
        return None
    try:
        numeric_score = int(float(str(score)))
    except (ValueError, TypeError):
        return None
    for low, high, nta_level in _NTA_RANGES.get(subject, {}).get(pre_level, []):
        if low <= numeric_score <= high:
            return nta_level
    return None


def _race_code_to_drc(race_code: str | None) -> dict:
    """Map a California 3-digit race code to the DRC race Y/N fields."""
    fields = {
        'American Indian or Alaskan Native': 'N',
        'Asian': 'N',
        'Black or African American': 'N',
        'Native Hawaiian or Other Pacific Islander': 'N',
        'White': 'N',
        'Multiracial': 'N',
        'Other': 'N',
    }
    if not race_code:
        return fields
    prefix = str(race_code)[:1]
    mapping = {
        '1': 'American Indian or Alaskan Native',
        '2': 'Asian',
        '3': 'Black or African American',
        '4': 'Native Hawaiian or Other Pacific Islander',
        '5': 'Asian',  # Filipino
        '7': 'White',
        '8': 'Multiracial',
        '9': 'Other',
    }
    field = mapping.get(prefix)
    if field:
        fields[field] = 'Y'
    return fields


def stu_csv_creator_dict(file_path, header, d):
    with open(file_path, "w") as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction="ignore")
        writer.writeheader()

        for row in d:
            writer.writerow(row)


def export_1112() -> None:
    """
    Generates a file TABE_students_1112.csv in the output folder, properly formatted for importing to DRC Insight.
    """
    filename = "TABE_students_1112.csv"
    header = [
    "District Code", "School Code", "Student ID", "Student Last Name", 
    "Student First Name", "Student Middle Initial", "Gender", "Date of Birth", 
    "Ethnicity", "Race - American Indian or Alaskan Native", "Race - Asian", 
    "Race - Black or African American", "Race - Native Hawaiian or Other Pacific Islander", 
    "Race - Caucasian", "Race - Other", "Public Assistance Status", "IEP", "504", 
    "LEP/ELL", "Program", "Additional Program", "ESL Status", "Labor Force Status", 
    "HSE Certificate", "HS Diploma", "Classified Accommodation - Reading", 
    "Classified Accommodation - Mathematics", "Classified Accommodation - Language"
]
    file_path = os.path.join(outputfolder, filename)

    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # Modify dictionary with new keys
    for s in students:
        c.print(f"Configuring row for {s['NameLast']}, {s['NameFirst']}")
        s["District Code"] = district_code
        s["School Code"] = school_code
        s["Student ID"] = s["TABEID"]
        s["Student Last Name"] = classNo + s["Platoon"] + " " + s.pop("NameLast")
        s["Student First Name"] = s.pop("NameFirst")
        s["Gender"] = s.pop("Gender")
        s["Date of Birth"] = s.pop("Birthday")
        s["Grade"] = s.pop("GradeLevel")
        s["Student_email"] = s.pop("SchoolEmail")

        if s["SpecialEducationIEP"] in ["Yes", "yes"]:
            s["IEP"] = "Y"
        else:
            s["IEP"] = "N"

        # if s["SpecialEducation504"] in ["Yes", "yes"]:
        #     s["504"] = "Y"
        # else:
        #     s["504"] = "N"

    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)

def export_1314() -> None:
    """
    Generates a file TABE_students_1314.csv in the output folder, properly formatted for importing to DRC Insight.
    """
    filename = "TABE_students_1314.csv"
    header = [
    "District Code", "School Code", "Student ID", "Last Name", "First Name",
    "Middle Initial", "Gender", "Date of Birth", "Country of Origin", "Ethnicity",
    "American Indian or Alaskan Native", "Asian", "Black or African American",
    "Native Hawaiian or Other Pacific Islander", "White", "Multiracial", "Other",
    "English First Language", "Home Language", "EL/ML", "ESL Status", "Disability",
    "504", "IEP", "Public Assistance Status", "Labor Force Status", "Program",
    "Additional Program", "Highest Level of Education", "Text-to-Speech",
    "Session Extension 1.25 Times", "Session Extension 1.5 Times",
    "Session Extension 2.0 Times", "Untimed Test", "Test Session Name", "Test",
    "Reading Level", "Mathematics Level", "Language Level", "FILLER"
]
    file_path = os.path.join(outputfolder, filename)

    students = filemaker_get_records(query=[{'StatusActive': 'Yes'}])

    # Modify dictionary with new keys
    for s in students:
        c.print(f"Configuring row for {s['NameLast']}, {s['NameFirst']}")
        s["District Code"] = district_code
        s["School Code"] = school_code
        s["Student ID"] = s["TABEID"]
        s["Last Name"] = (classNo + s["Platoon"] + " " + s.pop("NameLast"))[:20]
        s["First Name"] = s.pop("NameFirst")[:14]
        s["Gender"] = s.pop("Gender")
        s["Date of Birth"] = s.pop("Birthday")
        s["Grade"] = s.pop("GradeLevel")
        s["Student_email"] = s.pop("SchoolEmail")

        if s["SpecialEducationIEP"] in ["Yes", "yes"]:
            s["IEP"] = "Y"
        else:
            s["IEP"] = "N"

        # Test Session Assignment
        s["Test Session Name"] = "C" + classNo + "_FORM13_PLT" + s["Platoon"]
        s["Test"] = "L13" # assign auto-locator form 13


    c.print("\n")
    c.print(f"Creating file {filename} in {outputfolder}")
    stu_csv_creator_dict(file_path, header, students)


def export_post_tabe_14(round: int = 1) -> None:
    """
    Generates TABE_post_14_r{round}.csv for importing Form 14 post-test session
    assignments into DRC Insight. Produces one row per student per subject, using
    pre-test scaled scores and the NTA chart to determine the appropriate level.

    Session names follow the pattern: C{class}_14{subject}_{level}{round}
    e.g. C56_14READ_M1 for round 1, C56_14READ_M2 for round 2.
    """
    filename = f"TABE_post_14_r{round}.csv"
    header = [
        "District Code", "School Code", "Student ID", "Last Name", "First Name",
        "Middle Initial", "Gender", "Date of Birth", "Country of Origin", "Ethnicity",
        "American Indian or Alaskan Native", "Asian", "Black or African American",
        "Native Hawaiian or Other Pacific Islander", "White", "Multiracial", "Other",
        "English First Language", "Home Language", "EL/ML", "ESL Status", "Disability",
        "504", "IEP", "Public Assistance Status", "Labor Force Status", "Program",
        "Additional Program", "Highest Level of Education", "Text-to-Speech",
        "Session Extension 1.25 Times", "Session Extension 1.5 Times",
        "Session Extension 2.0 Times", "Untimed Test", "Test Session Name", "Test",
        "Reading Level", "Mathematics Level", "Language Level", "FILLER"
    ]
    file_path = os.path.join(outputfolder, filename)
    class_number = int(classNo)

    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD
        )
        cursor = connection.cursor(dictionary=True)

        # --- Query 1: pre-test assessment records ---
        cursor.execute(f"""
            SELECT
                at.STUDENT_ID AS tabeid,
                at.SUBTEST,
                at.SCALED_SCORE,
                at.NAME_LEVEL
            FROM Assessment_TABE at
            INNER JOIN Assessment_TABE_Cycle_Detail atcd ON at.id = atcd.assessment_tabe_id
            INNER JOIN Cycle_Detail cd ON atcd.cycle_detail_id = cd.id
            WHERE cd.class = {class_number}
                AND cd.status = '1'
                AND cd.program = 'residential'
                AND at.test_usage = 'PRE';
        """)
        assessment_records = cursor.fetchall()
        c.print(f"Retrieved {len(assessment_records)} pre-test assessment records.")

        # --- Query 2: student demographics ---
        cursor.execute(f"""
            SELECT
                cd.tabeid,
                cd.platoon,
                cd.is_hispanic,
                cd.race_code,
                cd.el_classification,
                cd.has_iep,
                cd.sped_iep,
                cd.has_504_plan,
                cd.sped_504,
                cd.program,
                p.first_name,
                p.last_name,
                p.middle_name,
                p.gender,
                p.birth_date
            FROM Cycle_Detail cd
            INNER JOIN Person p ON cd.person_id = p.id
            WHERE cd.class = {class_number}
                AND cd.status = '1'
                AND cd.program = 'residential';
        """)
        demographics = {row['tabeid']: row for row in cursor.fetchall()}
        c.print(f"Retrieved demographics for {len(demographics)} students.")

    except Error as e:
        c.print(f"[bold red]MySQL error: {e}[/bold red]")
        raise
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    # --- Build NTA assignments: {tabeid: {subject: level}} ---
    assignments: dict[int, dict[str, str]] = {}
    subject_map = {'Reading': 'READ', 'Mathematics': 'MATH', 'Language': 'LANG'}

    for record in assessment_records:
        tabeid = record['tabeid']
        subtest = record['SUBTEST']
        subject = subject_map.get(subtest)
        if not subject:
            c.print(f"[yellow]Unknown subtest '{subtest}' for TABEID {tabeid}. Skipping.[/yellow]")
            continue

        scaled_score = record['SCALED_SCORE']
        if scaled_score == 'N/A':
            c.print(f"[yellow]TABEID {tabeid} has no statistically significant {subtest} score (N/A). Skipping.[/yellow]")
            continue

        level = _calculate_post_tabe_level(record['NAME_LEVEL'], scaled_score, subject)
        if not level:
            c.print(f"[yellow]Could not determine NTA level for TABEID {tabeid} ({subtest}, level {record['NAME_LEVEL']}, score {scaled_score}). Skipping.[/yellow]")
            continue

        assignments.setdefault(tabeid, {})[subject] = level

    # --- Write CSV rows: one per (student, subject) ---
    rows = []
    for tabeid, subject_levels in assignments.items():
        demo = demographics.get(tabeid)
        if not demo:
            c.print(f"[yellow]No demographics found for TABEID {tabeid}. Skipping.[/yellow]")
            continue

        # IEP: prefer new boolean field, fall back to legacy string
        if demo['has_iep'] is not None:
            iep = 'Y' if demo['has_iep'] else 'N'
        else:
            iep = 'Y' if str(demo.get('sped_iep', '') or '').lower() in ('yes', 'y') else 'N'

        # 504: prefer new boolean field, fall back to legacy string
        if demo['has_504_plan'] is not None:
            s504 = 'Y' if demo['has_504_plan'] else 'N'
        else:
            s504 = 'Y' if str(demo.get('sped_504', '') or '').lower() in ('yes', 'y') else 'N'

        # EL/ML: treat L/R/E classifications as active EL
        el_ml = 'Y' if demo.get('el_classification') in ('L', 'R', 'E') else 'N'

        race_fields = _race_code_to_drc(demo.get('race_code'))

        dob = demo['birth_date']
        dob_str = dob.strftime('%m/%d/%Y') if dob else ''

        last_name = (str(classNo) + str(demo['platoon'] or '') + ' ' + (demo['last_name'] or ''))[:20]
        first_name = (demo['first_name'] or '')[:14]
        middle_initial = (demo['middle_name'] or '')[:1]

        base_row = {
            'District Code': district_code,
            'School Code': school_code,
            'Student ID': tabeid,
            'Last Name': last_name,
            'First Name': first_name,
            'Middle Initial': middle_initial,
            'Gender': demo['gender'] or '',
            'Date of Birth': dob_str,
            'Country of Origin': '',
            'Ethnicity': 'Y' if demo.get('is_hispanic') else 'N',
            **race_fields,
            'English First Language': '',
            'Home Language': '',
            'EL/ML': el_ml,
            'ESL Status': '',
            'Disability': '',
            '504': s504,
            'IEP': iep,
            'Public Assistance Status': '',
            'Labor Force Status': '',
            'Program': '',
            'Additional Program': '',
            'Highest Level of Education': '',
            'Text-to-Speech': '',
            'Session Extension 1.25 Times': '',
            'Session Extension 1.5 Times': '',
            'Session Extension 2.0 Times': '',
            'Untimed Test': '',
            'FILLER': '',
        }

        for subject, level in subject_levels.items():
            session_name = f"C{classNo}_14{subject}_{level}{round}"
            row = {
                **base_row,
                'Test Session Name': session_name,
                'Test': 'T14',
                'Reading Level': f'14{level}' if subject == 'READ' else '',
                'Mathematics Level': f'14{level}' if subject == 'MATH' else '',
                'Language Level': f'14{level}' if subject == 'LANG' else '',
            }
            rows.append(row)
            c.print(f"  {demo['last_name']}, {demo['first_name']} → {session_name}")

    c.print(f"\nWriting {len(rows)} rows to {filename}...")
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    c.print(f"[green]Done! File saved to {file_path}[/green]")


def export_retake_tabe_14(session_suffix: int = 2) -> None:
    """
    Generates TABE_retake_14_s{session_suffix}.csv for importing Form 14 retake
    session assignments into DRC Insight, and TABE_retake_14_s{session_suffix}_roster.csv
    as a student roster sorted by group then last name.

    Includes students who:
    - Have N/A in any post-test scale score (no statistically significant result), OR
    - Did not improve on average across subjects (avg post − pre scale score diff ≤ 0)

    Session names follow the pattern: C{class}_14{subject}_{level}{session_suffix}
    e.g. C56_14READ_M2 for session_suffix=2.
    """
    filename = f"TABE_retake_14_s{session_suffix}.csv"
    roster_filename = f"TABE_retake_14_s{session_suffix}_roster.csv"
    header = [
        "District Code", "School Code", "Student ID", "Last Name", "First Name",
        "Middle Initial", "Gender", "Date of Birth", "Country of Origin", "Ethnicity",
        "American Indian or Alaskan Native", "Asian", "Black or African American",
        "Native Hawaiian or Other Pacific Islander", "White", "Multiracial", "Other",
        "English First Language", "Home Language", "EL/ML", "ESL Status", "Disability",
        "504", "IEP", "Public Assistance Status", "Labor Force Status", "Program",
        "Additional Program", "Highest Level of Education", "Text-to-Speech",
        "Session Extension 1.25 Times", "Session Extension 1.5 Times",
        "Session Extension 2.0 Times", "Untimed Test", "Test Session Name", "Test",
        "Reading Level", "Mathematics Level", "Language Level", "FILLER"
    ]
    roster_header = ["Last Name", "First Name", "Group", "Platoon", "TABEID", "Reading", "Mathematics", "Language"]
    file_path = os.path.join(outputfolder, filename)
    roster_path = os.path.join(outputfolder, roster_filename)
    class_number = int(classNo)
    subject_map = {'Reading': 'READ', 'Mathematics': 'MATH', 'Language': 'LANG'}

    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            database=MYSQL_DATABASE,
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD
        )
        cursor = connection.cursor(dictionary=True)

        cursor.execute(f"""
            SELECT
                at.STUDENT_ID AS tabeid,
                at.SUBTEST,
                at.SCALED_SCORE,
                at.NAME_LEVEL
            FROM Assessment_TABE at
            INNER JOIN Assessment_TABE_Cycle_Detail atcd ON at.id = atcd.assessment_tabe_id
            INNER JOIN Cycle_Detail cd ON atcd.cycle_detail_id = cd.id
            WHERE cd.class = {class_number}
                AND cd.status = '1'
                AND cd.program = 'residential'
                AND at.test_usage = 'PRE';
        """)
        pre_assessment_records = cursor.fetchall()
        c.print(f"Retrieved {len(pre_assessment_records)} pre-test assessment records.")

        cursor.execute(f"""
            SELECT
                at.STUDENT_ID AS tabeid,
                at.SUBTEST,
                at.SCALED_SCORE,
                at.NAME_LEVEL
            FROM Assessment_TABE at
            INNER JOIN Assessment_TABE_Cycle_Detail atcd ON at.id = atcd.assessment_tabe_id
            INNER JOIN Cycle_Detail cd ON atcd.cycle_detail_id = cd.id
            WHERE cd.class = {class_number}
                AND cd.status = '1'
                AND cd.program = 'residential'
                AND at.test_usage = 'POST';
        """)
        post_assessment_records = cursor.fetchall()
        c.print(f"Retrieved {len(post_assessment_records)} post-test assessment records.")

        cursor.execute(f"""
            SELECT
                cd.tabeid,
                cd.platoon,
                cd.`group`,
                cd.is_hispanic,
                cd.race_code,
                cd.el_classification,
                cd.has_iep,
                cd.sped_iep,
                cd.has_504_plan,
                cd.sped_504,
                cd.program,
                p.first_name,
                p.last_name,
                p.middle_name,
                p.gender,
                p.birth_date
            FROM Cycle_Detail cd
            INNER JOIN Person p ON cd.person_id = p.id
            WHERE cd.class = {class_number}
                AND cd.status = '1'
                AND cd.program = 'residential';
        """)
        demographics = {row['tabeid']: row for row in cursor.fetchall()}
        c.print(f"Retrieved demographics for {len(demographics)} students.")

    except Error as e:
        c.print(f"[bold red]MySQL error: {e}[/bold red]")
        raise
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

    # Build pre-test lookup: {tabeid: {subject: {'score': ..., 'level': ...}}}
    pre_scores: dict[int, dict[str, dict]] = {}
    for record in pre_assessment_records:
        tabeid = record['tabeid']
        subject = subject_map.get(record['SUBTEST'])
        if not subject or record['SCALED_SCORE'] == 'N/A':
            continue
        pre_scores.setdefault(tabeid, {})[subject] = {
            'score': record['SCALED_SCORE'],
            'level': record['NAME_LEVEL'],
        }

    # Build post-test lookup: {tabeid: {subject: score_or_None}}
    # None indicates N/A (no statistically significant result)
    post_scores: dict[int, dict[str, object]] = {}
    for record in post_assessment_records:
        tabeid = record['tabeid']
        subject = subject_map.get(record['SUBTEST'])
        if not subject:
            continue
        score = None if record['SCALED_SCORE'] == 'N/A' else record['SCALED_SCORE']
        post_scores.setdefault(tabeid, {})[subject] = score

    # Determine retake subjects per student
    # A subject is included when: post score is N/A (use pre-test data for level),
    # or post score <= pre score (no improvement; use post score for level).
    # {tabeid: {subject: {'score': ..., 'level': ...}}}
    retake_map: dict[int, dict[str, dict]] = {}

    for tabeid, demo in demographics.items():
        pre = pre_scores.get(tabeid, {})
        post = post_scores.get(tabeid, {})

        # Gate: only include students whose average valid post score decreased.
        # avg_diff is None when all post scores are N/A (no valid pairs to average),
        # which also qualifies since the student couldn't be measured.
        diffs = []
        for subj in ['READ', 'MATH', 'LANG']:
            if subj in pre and subj in post and post[subj] is not None:
                try:
                    diffs.append(float(post[subj]) - float(pre[subj]['score']))
                except (ValueError, TypeError):
                    pass
        avg_diff = sum(diffs) / len(diffs) if diffs else None
        if avg_diff is not None and avg_diff > 0:
            continue

        subjects_for_retake: dict[str, dict] = {}

        for subj in ['READ', 'MATH', 'LANG']:
            if subj not in pre or subj not in post:
                continue
            if post[subj] is None:
                # N/A: assign based on pre-test score (expected next level)
                subjects_for_retake[subj] = pre[subj].copy()
            else:
                try:
                    if float(post[subj]) <= float(pre[subj]['score']):
                        subjects_for_retake[subj] = {
                            'score': post[subj],
                            'level': pre[subj]['level'],
                        }
                except (ValueError, TypeError):
                    pass

        if subjects_for_retake:
            retake_map[tabeid] = subjects_for_retake

    c.print(f"\n{len(retake_map)} students identified for retake.")

    rows = []
    roster_rows = []

    for tabeid, subject_data in retake_map.items():
        demo = demographics.get(tabeid)
        if not demo:
            continue

        if demo['has_iep'] is not None:
            iep = 'Y' if demo['has_iep'] else 'N'
        else:
            iep = 'Y' if str(demo.get('sped_iep', '') or '').lower() in ('yes', 'y') else 'N'

        if demo['has_504_plan'] is not None:
            s504 = 'Y' if demo['has_504_plan'] else 'N'
        else:
            s504 = 'Y' if str(demo.get('sped_504', '') or '').lower() in ('yes', 'y') else 'N'

        el_ml = 'Y' if demo.get('el_classification') in ('L', 'R', 'E') else 'N'
        race_fields = _race_code_to_drc(demo.get('race_code'))

        dob = demo['birth_date']
        dob_str = dob.strftime('%m/%d/%Y') if dob else ''

        last_name = (str(classNo) + str(demo['platoon'] or '') + ' ' + (demo['last_name'] or ''))[:20]
        first_name = (demo['first_name'] or '')[:14]
        middle_initial = (demo['middle_name'] or '')[:1]

        base_row = {
            'District Code': district_code,
            'School Code': school_code,
            'Student ID': tabeid,
            'Last Name': last_name,
            'First Name': first_name,
            'Middle Initial': middle_initial,
            'Gender': demo['gender'] or '',
            'Date of Birth': dob_str,
            'Country of Origin': '',
            'Ethnicity': 'Y' if demo.get('is_hispanic') else 'N',
            **race_fields,
            'English First Language': '',
            'Home Language': '',
            'EL/ML': el_ml,
            'ESL Status': '',
            'Disability': '',
            '504': s504,
            'IEP': iep,
            'Public Assistance Status': '',
            'Labor Force Status': '',
            'Program': '',
            'Additional Program': '',
            'Highest Level of Education': '',
            'Text-to-Speech': '',
            'Session Extension 1.25 Times': '',
            'Session Extension 1.5 Times': '',
            'Session Extension 2.0 Times': '',
            'Untimed Test': '',
            'FILLER': '',
        }

        assigned_subjects: dict[str, str] = {}  # subject → session_name
        for subject, data in subject_data.items():
            level = _calculate_post_tabe_level(data['level'], data['score'], subject)
            if not level:
                c.print(f"[yellow]Could not determine NTA level for TABEID {tabeid} ({subject}, level {data['level']}, score {data['score']}). Skipping subject.[/yellow]")
                continue
            session_name = f"C{classNo}_14{subject}_{level}{session_suffix}"
            row = {
                **base_row,
                'Test Session Name': session_name,
                'Test': 'T14',
                'Reading Level': f'14{level}' if subject == 'READ' else '',
                'Mathematics Level': f'14{level}' if subject == 'MATH' else '',
                'Language Level': f'14{level}' if subject == 'LANG' else '',
            }
            rows.append(row)
            assigned_subjects[subject] = session_name
            c.print(f"  {demo['last_name']}, {demo['first_name']} → {session_name}")

        if assigned_subjects:
            roster_rows.append({
                'Last Name': demo['last_name'] or '',
                'First Name': demo['first_name'] or '',
                'Group': demo.get('group') or '',
                'Platoon': demo.get('platoon') or '',
                'TABEID': tabeid,
                'Reading': 'Y' if 'READ' in assigned_subjects else '',
                'Mathematics': 'Y' if 'MATH' in assigned_subjects else '',
                'Language': 'Y' if 'LANG' in assigned_subjects else '',
            })

    roster_rows.sort(key=lambda r: (str(r['Group']), r['Last Name']))

    c.print(f"\nWriting {len(rows)} assignment rows to {filename}...")
    with open(file_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    c.print(f"[green]Assignment file saved to {file_path}[/green]")

    c.print(f"Writing {len(roster_rows)} roster rows to {roster_filename}...")
    with open(roster_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=roster_header, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(roster_rows)
    c.print(f"[green]Roster saved to {roster_path}[/green]")


def main():
    while (True):
        c.print("\n")
        c.rule(title="TABE Online Export")
        c.print("1: Generate TABE FORM 11/12 export file")
        c.print("2: Generate TABE FORM 13/14 pre-test export file")
        c.print("3: Generate TABE FORM 14 post-test assignment file")
        c.print("4: Generate TABE FORM 14 retake assignment file")
        c.print("5: Exit")

        option = Prompt.ask("Enter your choice:", choices=["1", "2", "3", "4", "5"])

        if option == "1":
            export_1112()
        elif option == "2":
            export_1314()
        elif option == "3":
            round_num = Prompt.ask("Round number", default="1")
            export_post_tabe_14(round=int(round_num))
        elif option == "4":
            suffix = Prompt.ask("Session suffix (2 for first retake, 3 for second, etc.)", default="2")
            export_retake_tabe_14(session_suffix=int(suffix))
        elif option == "5":
            exit()


if __name__ == "__main__":
    main()
