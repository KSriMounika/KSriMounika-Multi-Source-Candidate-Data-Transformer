import argparse
import json
import logging
import sys
from src.pipeline import run_pipeline

logging.basicConfig(level=logging.WARNING)

def main():
    parser = argparse.ArgumentParser(description="Multi-Source Candidate Data Transformer")
    parser.add_argument("--csv", default="data/input/recruiter.csv", help="Path to recruiter CSV file")
    parser.add_argument("--resume", default="data/input/resume.pdf", help="Path to resume PDF file")
    parser.add_argument("--config", default=None, help="Path to custom projection config JSON")
    
    args = parser.parse_args()

    print("Initializing Multi-Source Candidate Data Transformer...")
    
    # 1. Run Pipeline with Default Schema if no custom config is provided
    if not args.config:
        try:
            with open("schemas/output_schema.json", "r") as f:
                default_schema = json.load(f)
        except FileNotFoundError as e:
            print(f"Failed to load default schema: {e}")
            sys.exit(1)
            
        default_config = {
            "fields": [
                {"path": "candidate_id"},
                {"path": "full_name"},
                {"path": "emails"},
                {"path": "phones"},
                {"path": "location"},
                {"path": "links"},
                {"path": "headline"},
                {"path": "years_experience"},
                {"path": "skills"},
                {"path": "experience"},
                {"path": "education"},
            ],
            "include_provenance": True,
            "include_confidence": True,
            "on_missing": "omit"
        }
        
        try:
            print("\n--- Running Default Schema ---")
            default_result = run_pipeline(args.csv, args.resume, default_config, default_schema)
            print("Success! Generated schema-valid default profile.")
            print(json.dumps(default_result, indent=2))
            with open("data/output/default_profile.json", "w") as f:
                json.dump(default_result, f, indent=2)
        except Exception as e:
            print(f"\nPipeline failed: {e}")
            
    # 2. Run Pipeline with Custom Config if provided
    else:
        try:
            with open(args.config, "r") as f:
                custom_config = json.load(f)
            # For this demo, we validate against custom_schema.json when using the sample config
            with open("schemas/custom_schema.json", "r") as f:
                custom_schema = json.load(f)
        except FileNotFoundError as e:
            print(f"Failed to load custom config/schema: {e}")
            sys.exit(1)
            
        try:
            print("\n--- Running Custom Projection Config ---")
            custom_result = run_pipeline(args.csv, args.resume, custom_config, custom_schema)
            print("Success! Generated schema-valid custom profile.")
            print(json.dumps(custom_result, indent=2))
            with open("data/output/custom_profile.json", "w") as f:
                json.dump(custom_result, f, indent=2)
        except Exception as e:
            print(f"\nPipeline failed: {e}")

if __name__ == "__main__":
    main()
