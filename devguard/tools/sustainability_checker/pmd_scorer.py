#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import argparse
from collections import defaultdict
import os

# --- CUSTOMIZABLE SECTION ---
# Define your PMD rules and their corresponding "Potential Eco-Impact Points".
# The keys are the 'rule' attribute values from the PMD XML report.
# The values (points) reflect how much a rule violation might contribute to
# resource inefficiency (CPU, memory), which can correlate with energy consumption.
# You'll need to inspect your PMD XML output to get the exact rule names.
RULE_WEIGHTS = {
    # Performance-related (examples, rule names might vary based on your PMD ruleset)
    # These can directly impact CPU cycles and memory, hence energy use.
    "AvoidInstantiatingObjectsInLoops": 10,
    "UseStringBufferForStringAppendsInLoops": 8, # Or e.g., "InefficientStringBuffering"
    "AppendCharacterWithChar": 5,
    "AvoidBranchingStatementAsLastInLoop": 3,
    "OptimizeStartsWith": 4,
    "AvoidFileStream": 3, # If not handled carefully, can be inefficient
    "UseConcurrentHashMap": 2,

    # Complexity (can make code harder to optimize and hide inefficiencies)
    "CyclomaticComplexity": 7,
    "NPathComplexity": 7,
    "CognitiveComplexity": 8,
    "ExcessiveMethodLength": 5,
    "ExcessiveParameterList": 4,
    "TooManyMethods": 3,

    # General "bad practices" that *could* indirectly lead to inefficiency or resource issues
    "SimplifyBooleanExpressions": 2,
    "AvoidDeeplyNestedIfStmts": 4,
    "EmptyCatchBlock": 3, # Can hide errors, potentially leading to resource leaks or inefficient recovery
    "FinalizeDoesNotCallSuperFinalize": 2,
    "CloseResource": 9, # Critical for preventing resource leaks

    # Unused code (contributes to code bloat, compilation time, and developer cognitive load)
    "UnusedLocalVariable": 1,
    "UnusedPrivateMethod": 2,
    "UnusedFormalParameter": 1,
    "UnusedPrivateField": 1,
}

# PMD XML reports often use a default namespace.
NAMESPACES = {'pmd': 'http://pmd.sourceforge.net/report/2.0.0'}
# --- END CUSTOMIZABLE SECTION ---

def parse_pmd_report(xml_file_path):
    """
    Parses a PMD XML report and calculates a potential eco-impact score.

    Args:
        xml_file_path (str): Path to the PMD XML report file.

    Returns:
        tuple: (total_score, violation_details, file_scores)
               total_score (int): The total calculated score.
               violation_details (defaultdict): Counts and scores per rule.
               file_scores (defaultdict): Scores per file.
    """
    if not os.path.exists(xml_file_path):
        print(f"Error: File not found at {xml_file_path}")
        return 0, defaultdict(lambda: {'count': 0, 'score': 0}), defaultdict(int)

    total_score = 0
    violation_details = defaultdict(lambda: {'count': 0, 'score': 0})
    file_scores = defaultdict(int)

    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        file_elements = root.findall('pmd:file', NAMESPACES)
        if not file_elements and root.tag.endswith('pmd'):
            file_elements = root.findall('file')

        for file_element in file_elements:
            file_name = file_element.get('name', 'UnknownFile')
            current_file_score = 0

            violations = file_element.findall('pmd:violation', NAMESPACES)
            if not violations and NAMESPACES['pmd']:
                 violations = file_element.findall(f".//{{{NAMESPACES['pmd']}}}violation")
            if not violations:
                 violations = file_element.findall('.//violation')

            for violation in violations:
                rule_name = violation.get('rule')
                if rule_name in RULE_WEIGHTS:
                    points = RULE_WEIGHTS[rule_name]
                    total_score += points
                    current_file_score += points

                    violation_details[rule_name]['count'] += 1
                    violation_details[rule_name]['score'] += points
            
            if current_file_score > 0:
                file_scores[file_name] = current_file_score

    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return 0, violation_details, file_scores
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 0, violation_details, file_scores

    return total_score, violation_details, file_scores

def main():
    parser = argparse.ArgumentParser(
        description="🌿 Process a PMD XML report to estimate a 'Potential Eco-Impact Score' for your Java code."
    )
    parser.add_argument("pmd_report_file", help="Path to the PMD XML report file.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed breakdown per rule and per file.")

    args = parser.parse_args()

    total_score, violation_details, file_scores = parse_pmd_report(args.pmd_report_file)

    print("\n--- 🌿 PMD Sustainability & Resource Efficiency Analysis 🌿 ---")
    print(f"\n🌍 Total Potential Eco-Impact Score: {total_score} points")
    if total_score == 0 and not violation_details:
        print("Excellent! No relevant rule violations found based on the current configuration. Keep up the green coding! 👍")


    if args.verbose:
        if violation_details:
            print("\n💡 Rule-Based Sustainability Insights (Violations contributing to score):")
            sorted_rules = sorted(violation_details.items(), key=lambda item: item[1]['score'], reverse=True)
            for rule_name, details in sorted_rules:
                print(f"  - Rule: {rule_name:<40} | Occurrences: {details['count']:<4} | Impact Points: {details['score']}")
        elif total_score > 0 : # Some score but no details somehow (should not happen if score > 0)
             print("\nNo detailed rule violations to show, but a score was calculated.")


        if file_scores:
            print("\n💻 File Hotspots (Files with highest Potential Eco-Impact Score):")
            sorted_files = sorted(file_scores.items(), key=lambda item: item[1], reverse=True)
            for file_name, score in sorted_files:
                short_file_name = os.path.relpath(file_name) if len(os.path.relpath(file_name)) < len(file_name) else file_name
                print(f"  - File: {short_file_name:<70} | Impact Points: {score}")
        elif total_score > 0:
             print("\nNo specific file hotspots identified, but a score was calculated.")


    print("\n🌱 Our Planet, Our Code:")
    print("This score is a heuristic. It helps identify code patterns that *may* lead to")
    print("higher energy and resource consumption. Lower scores suggest more resource-efficient code.")
    print("Fine-tune RULE_WEIGHTS in the script to reflect your project's specific sustainability goals.")
    print("More efficient code is greener code! ♻️")

if __name__ == "__main__":
    main()
