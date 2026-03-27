# aws-project-1
# requirements 
pip install -r requirements.txt
# Submit file for review
aws s3 cp {insert_json_or_csv_file} s3://sam-app-feedbackbucket-6l36mzbhlexz/incoming/{json_or_csv_file}
# Review feedback manually
aws lambda invoke \\
  --function-name sam-app-SubmitReviewFunction-0UnenRXP12Vv \\
  --cli-binary-format raw-in-base64-out \\
  --payload '{
    "review_id": "insert_id_here",
    "decision": "APPROVED",
    "reviewer": "insert_email_address"
  }' \\
  response.json
